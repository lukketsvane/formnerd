import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'firmware/A1_Bench_Camera/A1_Bench_Camera.ino'
PRE = '#include <cstdint>\n#include <cassert>\n#include <cstdio>\n#include <cstring>\n#include <deque>\n#include <string>\nusing String=std::string;\nconstexpr bool HIGH=true,LOW=false;\nconstexpr int PIXFORMAT_JPEG=1;\nconstexpr uint8_t SHUTTER_PIN=13;\nconstexpr uint32_t DEBOUNCE_MS=40;\nstruct SerialType { void println(const String&){} template<class...T> void printf(const char*,T...){} } Serial;\nstruct ServerType { void handleClient(){} } server;\nstruct camera_fb_t { uint8_t* buf; size_t len; int format; };\nstd::deque<camera_fb_t*> frames;\nuint32_t fakeTime=0;\nbool fakePin=HIGH;\nuint32_t millis(){return fakeTime;}\nbool digitalRead(uint8_t){return fakePin;}\nvoid delay(int){}\ncamera_fb_t* esp_camera_fb_get(){if(frames.empty())return nullptr;auto p=frames.front();frames.pop_front();return p;}\nvoid esp_camera_fb_return(camera_fb_t* f){if(f->buf&&f->len<100)memset(f->buf,0xEE,f->len);}\nuint8_t destination[16]={};\nuint8_t* latestJpeg=destination;\nsize_t latestCapacity=sizeof(destination),latestLength=0;\nuint32_t captureCount=0,capturedAt=0,changedAt=0;\nbool cameraReady=true,accessPointReady=false,rawButton=HIGH,stableButton=HIGH;\nString lastStatus;\n'
POST = 'void queueImage(){static uint8_t data[4];data[0]=0xFF;data[1]=0xD8;data[2]=0xFF;data[3]=0xD9;static camera_fb_t frame={data,4,PIXFORMAT_JPEG};frames.push_back(nullptr);frames.push_back(&frame);}\nvoid sample(uint32_t t,bool pin){fakeTime=t;fakePin=pin;loop();}\nint main(){\nqueueImage();assert(captureImage());assert(captureCount==1&&latestLength==4);assert(destination[0]==0xFF&&destination[3]==0xD9);\nuint8_t tooBig[24]={};camera_fb_t bad={tooBig,24,PIXFORMAT_JPEG};frames.push_back(nullptr);frames.push_back(&bad);assert(!captureImage());assert(captureCount==1&&latestLength==4&&destination[0]==0xFF);\ncamera_fb_t nullBuf={nullptr,4,PIXFORMAT_JPEG};frames.push_back(nullptr);frames.push_back(&nullBuf);assert(!captureImage());assert(captureCount==1);\nassert(!captureImage());assert(captureCount==1);\ncameraReady=false;assert(!captureImage());cameraReady=true;\nqueueImage();sample(100,LOW);sample(110,HIGH);sample(120,LOW);sample(159,LOW);assert(captureCount==1);sample(160,LOW);assert(captureCount==2);sample(400,LOW);assert(captureCount==2);\nsample(500,HIGH);sample(540,HIGH);queueImage();sample(600,LOW);sample(640,LOW);assert(captureCount==3);\nsample(700,HIGH);sample(740,HIGH);queueImage();sample(0xFFFFFFF0u,LOW);sample(0x18u,LOW);assert(captureCount==4);\nframes.clear();stableButton=LOW;rawButton=LOW;changedAt=0;sample(80,LOW);assert(captureCount==4);sample(100,HIGH);sample(140,HIGH);queueImage();sample(180,LOW);sample(220,LOW);assert(captureCount==5);\nprintf("{\\"passed\\":true,\\"cases\\":10}\\n");\n}\n'
UI = "const fs=require('fs'),vm=require('vm'),assert=require('assert');\nconst nodes={};for(const id of ['#capture','#status','#photo','#save'])nodes[id]={hidden:true,disabled:false,removeAttribute(k){delete this[k]}};\nlet state={camera:true,count:0,bytes:0,status:'Ready'};\nconst ctx={document:{querySelector:id=>nodes[id]},fetch:async path=>({ok:true,status:200,json:async()=>state,text:async()=>''}),setInterval:()=>0};\nvm.createContext(ctx);vm.runInContext(fs.readFileSync(process.argv[2],'utf8'),ctx);\nconst tick=()=>new Promise(r=>setImmediate(r));\n(async()=>{await tick();assert(nodes['#photo'].hidden);assert(nodes['#save'].hidden);state={camera:true,count:1,bytes:23000,status:'Capture OK'};await vm.runInContext('refresh()',ctx);assert.equal(nodes['#photo'].src,'/last.jpg?v=1');assert(!nodes['#photo'].hidden);assert(!nodes['#save'].hidden);state={camera:true,count:0,bytes:0,status:'Ready'};await vm.runInContext('refresh()',ctx);assert(nodes['#photo'].hidden);assert(nodes['#save'].hidden);assert.equal(nodes['#photo'].src,undefined);state={camera:false,count:0,bytes:0,status:'Camera initialisation failed'};await vm.runInContext('refresh()',ctx);assert(nodes['#capture'].disabled);assert(nodes['#status'].textContent.includes('Camera initialisation failed'));console.log(JSON.stringify({passed:true,cases:['empty-image-hidden','capture-updates-image','reset-clears-stale-image','camera-error-disables-button']}))})().catch(e=>{console.error(e);process.exit(1)});\n"

def main():
    source = SOURCE.read_text()
    start = source.index('bool captureImage() {')
    end = source.index('\nvoid sendPhoto', start)
    capture = source[start:end]
    loop = source[source.index('void loop() {'):]
    script_start = source.index('<script>') + len('<script>')
    script_end = source.index('</script>', script_start)
    assert '[hidden]{display:none!important}' in source
    with tempfile.TemporaryDirectory(prefix='a1-firmware-host-') as directory:
        work = Path(directory)
        cpp = work / 'logic.cpp'
        cpp.write_text(PRE + capture + '\n' + loop + '\n' + POST)
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-fsanitize=address,undefined', str(cpp), '-o', str(work / 'logic')], check=True, capture_output=True, text=True)
        environment = dict(os.environ)
        environment['ASAN_OPTIONS'] = 'detect_leaks=0'
        logic = subprocess.run([str(work / 'logic')], check=True, capture_output=True, text=True, env=environment)
        (work / 'page.js').write_text(source[script_start:script_end])
        (work / 'ui.cjs').write_text(UI)
        ui = subprocess.run(['node', str(work / 'ui.cjs'), str(work / 'page.js')], check=True, capture_output=True, text=True)
        report = {
            'source': str(SOURCE.relative_to(ROOT)),
            'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'passed': True,
            'logic': {
                'actual_source_functions_extracted': ['captureImage', 'loop'],
                'camera_and_gpio_simulated': True,
                'sanitizers': ['address', 'undefined'],
                'leak_sanitizer': 'disabled because sandbox /proc task access prevents leak-sanitizer execution',
                'cases': ['JPEG survives returned framebuffer mutation', 'oversized frame preserves previous image', 'null buffer rejected', 'null frame rejected', 'camera-not-ready rejected', 'contact bounce ignored until 40ms stable', 'held button captures once', 'release and second press capture again', 'millis wraparound', 'button held at boot waits for release'],
                'raw_result': json.loads(logic.stdout)
            },
            'ui': json.loads(ui.stdout),
            'hardware_flashed': False,
            'hardware_function_tested': False,
            'scope': 'Host-side simulations verify application logic only; not camera driver, Wi-Fi, physical electronics or exposure timing.'
        }
    (ROOT / 'verification/firmware-host-r02.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
