import argparse
import json
from pathlib import Path
import struct
import subprocess
import tempfile

import numpy as np
from PIL import Image
import vtk
from vtk.util.numpy_support import vtk_to_numpy


RASTER = r'''
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <vector>
int main(int argc, char** argv) {
    std::ifstream in(argv[1], std::ios::binary);
    uint32_t w, h, count;
    in.read(reinterpret_cast<char*>(&w), 4);
    in.read(reinterpret_cast<char*>(&h), 4);
    in.read(reinterpret_cast<char*>(&count), 4);
    float scale;
    in.read(reinterpret_cast<char*>(&scale), 4);
    std::vector<float> depth(size_t(w)*h, std::numeric_limits<float>::infinity());
    std::vector<float> normals(size_t(w)*h*3, 0.0f);
    std::vector<uint8_t> pixels(size_t(w)*h*3, 255);
    float v[27];
    for (uint32_t t=0; t<count; ++t) {
        in.read(reinterpret_cast<char*>(v), sizeof(v));
        float x0=v[0], y0=v[1], x1=v[9], y1=v[10], x2=v[18], y2=v[19];
        float den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2);
        if (std::abs(den)<0.000001f) continue;
        int ax=std::max(0, int(std::floor(std::min({x0,x1,x2}))));
        int bx=std::min(int(w)-1, int(std::ceil(std::max({x0,x1,x2}))));
        int ay=std::max(0, int(std::floor(std::min({y0,y1,y2}))));
        int by=std::min(int(h)-1, int(std::ceil(std::max({y0,y1,y2}))));
        for (int y=ay; y<=by; ++y) {
            for (int x=ax; x<=bx; ++x) {
                float px=x+0.5f, py=y+0.5f;
                float a=((y1-y2)*(px-x2)+(x2-x1)*(py-y2))/den;
                float b=((y2-y0)*(px-x2)+(x0-x2)*(py-y2))/den;
                float c=1.0f-a-b;
                if (a < -0.00001f || b < -0.00001f || c < -0.00001f) continue;
                float z=a*v[2]+b*v[11]+c*v[20];
                size_t i=size_t(y)*w+x;
                if (z>=depth[i]) continue;
                depth[i]=z;
                for (int k=0; k<3; ++k) {
                    float value=a*v[3+k]+b*v[12+k]+c*v[21+k];
                    pixels[i*3+k]=uint8_t(std::clamp(value*255.0f, 0.0f, 255.0f)+0.5f);
                    normals[i*3+k]=a*v[6+k]+b*v[15+k]+c*v[24+k];
                }
            }
        }
    }
    const float pi=3.14159265358979323846f;
    const float radii[3]={0.55f,1.15f,2.3f};
    for (uint32_t y=0; y<h; ++y) {
        for (uint32_t x=0; x<w; ++x) {
            size_t i=size_t(y)*w+x;
            if (!std::isfinite(depth[i])) continue;
            float nx=normals[i*3], ny=normals[i*3+1], nz=normals[i*3+2];
            float normal_length=std::sqrt(nx*nx+ny*ny+nz*nz);
            if (normal_length<0.00001f) continue;
            float occlusion=0;
            for (float radius:radii) {
                for (int d=0; d<12; ++d) {
                    float angle=2*pi*(d+0.25f)/12;
                    int ox=int(std::round(std::cos(angle)*radius*scale));
                    int oy=int(std::round(std::sin(angle)*radius*scale));
                    int sx=int(x)+ox, sy=int(y)+oy;
                    if (sx<0 || sy<0 || sx>=int(w) || sy>=int(h)) continue;
                    size_t j=size_t(sy)*w+sx;
                    if (!std::isfinite(depth[j])) continue;
                    float dx=ox/scale, dy=-oy/scale, dz=depth[j]-depth[i];
                    float distance=std::sqrt(dx*dx+dy*dy+dz*dz);
                    if (distance<0.05f || distance>4.5f) continue;
                    float above=(nx*dx+ny*dy+nz*dz)/normal_length-0.12f;
                    float cosine=std::max(0.0f,above/distance);
                    occlusion+=cosine*std::exp(-distance*distance/7.5f);
                }
            }
            float factor=1-std::clamp(0.8f*occlusion/36,0.0f,0.28f);
            for (int k=0; k<3; ++k) pixels[i*3+k]=uint8_t(pixels[i*3+k]*factor+0.5f);
        }
    }
    std::ofstream out(argv[2], std::ios::binary);
    out << "P6\n" << w << " " << h << "\n255\n";
    out.write(reinterpret_cast<char*>(pixels.data()), pixels.size());
    return in.good() && out.good() ? 0 : 1;
}
'''


def unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def load_part(path):
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(path))
    reader.MergingOn()
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(reader.GetOutputPort())
    normals.SetFeatureAngle(48)
    normals.SplittingOn()
    normals.ConsistencyOn()
    normals.AutoOrientNormalsOn()
    normals.ComputePointNormalsOn()
    normals.ComputeCellNormalsOff()
    normals.Update()
    poly = normals.GetOutput()
    if not poly.GetNumberOfPoints():
        raise ValueError(f"Empty mesh: {path}")
    points = vtk_to_numpy(poly.GetPoints().GetData()).astype(float)
    faces = vtk_to_numpy(poly.GetPolys().GetData()).reshape(-1, 4)[:, 1:]
    vectors = vtk_to_numpy(poly.GetPointData().GetNormals()).astype(float)
    return points, faces, vectors


def colors(normals, base, view, right, vertical):
    base = np.asarray(base[:3], dtype=float)
    if np.max(base) > 1:
        base /= 255
    key = unit(view * 0.6 - right * 0.7 + vertical * 1.0)
    fill = unit(view * 0.9 + right * 0.6 + vertical * 0.25)
    rim = unit(-view * 0.55 + right * 0.35 + vertical * 0.8)
    diffuse = 0.43 + 0.39 * np.maximum(normals @ key, 0)
    diffuse += 0.21 * np.maximum(normals @ fill, 0)
    diffuse += 0.06 * np.maximum(normals @ rim, 0)
    diffuse += 0.08 * np.maximum(normals @ view, 0)
    half = unit(key + view)
    specular = 0.04 * np.maximum(normals @ half, 0) ** 18
    return np.clip(base[None, :] * diffuse[:, None] + specular[:, None], 0, 1)


def render(parts, eye, target, output, raster, work, width, height, exploded=False, up=(0, 0, 1)):
    forward = unit(np.asarray(target) - np.asarray(eye))
    right = unit(np.cross(forward, up))
    vertical = unit(np.cross(right, forward))
    geometry = []
    all_projected = []
    for part in parts:
        points, faces, normals = part["mesh"]
        offset = np.asarray(part.get("explode", [0, 0, 0]), dtype=float) if exploded else np.zeros(3)
        points = points + offset
        projected = np.column_stack((points @ right, points @ vertical, points @ forward))
        projected_normals = np.column_stack((normals @ right, normals @ vertical, normals @ forward))
        geometry.append((projected, faces, colors(normals, part["color"], -forward, right, vertical), projected_normals))
        all_projected.append(projected)
    bounds = np.concatenate(all_projected)
    low = bounds[:, :2].min(axis=0)
    high = bounds[:, :2].max(axis=0)
    center = (low + high) / 2
    scale = min(width * 0.85 / (high[0] - low[0]), height * 0.85 / (high[1] - low[1]))
    count = sum(len(faces) for _, faces, _, _ in geometry)
    binary = work / "triangles.bin"
    ppm = work / "render.ppm"
    with binary.open("wb") as handle:
        handle.write(struct.pack("<III", width, height, count))
        handle.write(struct.pack("<f", scale))
        for projected, faces, rgb, normals in geometry:
            projected[:, 0] = (projected[:, 0] - center[0]) * scale + width / 2
            projected[:, 1] = height / 2 - (projected[:, 1] - center[1]) * scale
            vertices = np.concatenate((projected, rgb, normals), axis=1)
            handle.write(vertices[faces].astype("<f4").tobytes())
    subprocess.run([str(raster), str(binary), str(ppm)], check=True)
    with Image.open(ppm) as image:
        temporary_output = output.with_suffix('.write.png')
        image.resize((width // 2, height // 2), Image.Resampling.LANCZOS).save(temporary_output)
        with Image.open(temporary_output) as checked:
            checked.verify()
        temporary_output.replace(output)
    print(output, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--height", type=int, default=1200)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--only", choices=("hero", "front", "back", "left", "right", "top", "exploded"))
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = json.loads((root / "cad" / "assembly_manifest.json").read_text())
    parts = manifest["parts"] if isinstance(manifest, dict) else manifest
    parts = [dict(p) for p in parts if p.get("preview", True)]
    for part in parts:
        part["color"] = part.get("color", part.get("colorRGB", [0.68, 0.69, 0.69]))
        part["mesh"] = load_part(root / part["file"])
    output = args.output.resolve() if args.output else root / "preview"
    output.mkdir(parents=True, exist_ok=True)
    views = {
        "hero": ((-210, -340, 210), (0, -5, 52), (0, 0, 1), False),
        "back": ((0, 450, 52), (0, -5, 52), (0, 0, 1), False),
        "left": ((-450, -5, 52), (0, -5, 52), (0, 0, 1), False),
        "front": ((0, -450, 52), (0, -5, 52), (0, 0, 1), False),
        "right": ((450, -5, 52), (0, -5, 52), (0, 0, 1), False),
        "top": ((0, -5, 450), (0, -5, 52), (0, 1, 0), False),
        "exploded": ((-40, -440, 260), (0, -5, 52), (0, 0, 1), True),
    }
    with tempfile.TemporaryDirectory(prefix="entropi-render-") as temp:
        work = Path(temp)
        source = work / "raster.cpp"
        raster = work / "raster"
        source.write_text(RASTER)
        subprocess.run(["g++", "-O3", "-std=c++17", str(source), "-o", str(raster)], check=True)
        for name, (eye, target, up, exploded) in views.items():
            if args.only and args.only != name:
                continue
            render(parts, eye, target, output / f"{name}.png", raster, work, args.width * 2, args.height * 2, exploded, up)


if __name__ == "__main__":
    main()
