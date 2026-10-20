# A1 prøveprogram for ESP32-CAM

Dette programmet gir eit første kamerabilete i nettlesaren og ein fysisk utløysar. Det er laga for **AI Thinker ESP32-CAM med OV2640 og ESP32-CAM-MB**, utan microSD. Arduino IDE er programmet på PC-en. Eit separat Arduino-/Uno-kort trengst ikkje i denne oppkoplinga.

Programmet er ein benktest før innbygging. Det er ikkje ferdig programvare for batteridrift, USB-C-lading, USB-biletoverføring eller varig lagring.

## Før straum

1. Kontroller at kortet faktisk er ein AI Thinker-kompatibel ESP32-CAM. Kontroller kamerafleksen utan å trekkje han ut dersom han allereie sit rett.
2. Set CAM-kortet i MB-soklane etter dei faktiske pinnemerkingane. Alle pinnane skal treffe, utan éi rad forskyving. Kortrevisjonar kan ha ulik orientering.
3. La microSD-sporet vere tomt. Start utan utløysarleidningar.
4. Kople MB sin Micro-USB til PC-en med ein USB-datakabel. MB gir straum og USB-UART-programmering. Han er ikkje ein batteriladar.

## Arduino IDE

1. Installer Arduino IDE frå [Arduino](https://www.arduino.cc/en/software).
2. Legg `https://espressif.github.io/arduino-esp32/package_esp32_index.json` i **Additional Boards Manager URLs** i innstillingane.
3. Installer **esp32 by Espressif Systems** frå Boards Manager. Kompileringa er dokumentert i `../verification/firmware-r02.json`. Kamera-, Wi-Fi- og WebServer-biblioteka følgjer denne plattforma; denne skissa krev ingen separat kamerabibliotekinstallasjon.
4. Vel **AI Thinker ESP32-CAM** og serieporten som kjem fram når MB blir kopla til. MB er ikkje kortmodellen du skal velje.
5. Opne `A1_Bench_Camera/A1_Bench_Camera.ino`. Mappa og `.ino`-fila skal ha same namn. Dette er eit sjølvstendig program; du skal ikkje lime det inn i CameraWebServer.
6. Trykk **Verify** og deretter **Upload**. Bruk AI Thinker-profilen med PSRAM. Dersom val for partisjon er synleg, bruk standardprofilen/Huge APP med 3 MB app-plass.
7. Dersom opplasting står på `Connecting...`, hald **IO0/BOOT**, trykk og slepp **RST**, og slepp IO0 når tilkopling/opplasting startar. MB-revisjonar kan ha ulik automatisk reset. Etter opplasting skal IO0 vere sleppt; trykk RST for normal oppstart.
8. Opne Serial Monitor på **115200 baud**. Meldinga skal vise kamera klart og adressa til tilkoplingspunktet. Ved kamerafeil viser nettlesaren feilstatus, og knappen blir deaktivert.

## Første bilete

1. Kople telefonen eller PC-en til Wi-Fi **A1-Camera**.
2. Passordet i dette prøveprogrammet er **A1camera2026**. Dette er offentlege testinnstillingar, ikkje private brukarkontoopplysningar. Endre konstantane før bruk andre stader.
3. Vel å bli verande på nettet sjølv om telefonen seier at nettet manglar internett.
4. Opne **http://192.168.4.1/** i nettlesaren. Bruk adressa frå Serial Monitor dersom ho er annleis.
5. Trykk **Ta bilete**. Kontroller at teljaren aukar med éin og at motivet blir vist.
6. Trykk **Last ned siste JPEG**. Kontroller den nedlasta fila før du slår av straumen.

Det siste biletet ligg berre i RAM. Nytt bilete erstattar det førre. Straumbrot slettar biletet. Programmet tek stillbilete; det gir ikkje kontinuerleg video eller native USB-kamerafunksjon.

## Fysisk utløysar

Kople frå USB før du legg til leidningar.

| Frå | Til |
|---|---|
| ESP32-CAM, pin/pad merkt GPIO13 eller IO13 | Første kontakt på ein normalt open trykknapp |
| Andre brytarkontakt | ESP32-CAM GND |

Bruk merkinga på ditt kort, ikkje eit fysisk pinnenummer eller ei antatt side av teikninga. MB kan dekkje pinnane; faktisk tilkomst til GPIO13/GND og leidningsføring må kontrollerast før innbygging. Ikkje tving ekstra kontaktar ned i ein full sokkel.

Ein firebeint taktknapp har ofte to internt samankopla par. Finn med kontinuitetsmåling eit par som er ope utan trykk og lukkar når du trykkjer. Ikkje vel to bein som allereie er kopla saman. Brytarmodellen i Arduino-settet er ikkje stadfesta.

Programmet set GPIO13 til `INPUT_PULLUP`. Utløysing skjer når brytaren koplar signalet til GND (`LOW`). Ingen 5 V skal til GPIO13. IO0 og RST på MB er oppstarts-/resetknappar og skal ikkje brukast som denne utløysaren. GPIO13 blir også brukt av SD DATA3; denne versjonen initialiserer ikkje SD og føreset at ingen SD-kort er montert.

Kople USB til att. Trykk roleg éin gong og slepp heilt. Teljaren skal auke éin gong. Hald knappen inne: teljaren skal halde same verdi. Slepp, vent og trykk på nytt: teljaren skal auke éin gong til. Test minst ti trykk før du monterer elektronikken i huset.

Avprellinga krev 40 ms stabilt signal. Nettserveren er synkron; svært korte trykk medan ein klient overfører data kan gå tapt. Programmet kopierer eit kamerabilete når trykket blir registrert, men garanterer ikkje eit eksakt eksponeringstidspunkt etter trykket. Dette må vurderast dersom presis lukkarrespons er eit prosjektkrav.

## Funksjonar og minne

| Tilgang | Funksjon |
|---|---|
| `GET /` | Kameraside med knapp, teljar, status og siste bilete |
| `POST /capture` | Ta eitt stillbilete |
| `GET /status` | Kamera-/biletestatus som JSON |
| `GET /last.jpg` | Siste JPEG, eller HTTP 404 dersom ingen er tekne |
| `GET /download` | Siste JPEG som `A1-<teljar>.jpg` |

Med PSRAM: VGA (640 x 480), to kamerabufferar og maksimalt 256 KiB for det siste lagra JPEG-biletet. Utan PSRAM: QVGA (320 x 240), éin kamerabuffer og maksimalt 48 KiB for siste JPEG. Bilete over grensa blir avviste, og siste gyldige bilete blir behalde. Feil på kamerainitialisering eller fotobuffer blir vist via Serial og nettstatus. JPEG-data blir kopierte før kamerabufferen blir returnert til drivaren. All tilgang til siste JPEG skjer i same hovudløkke som den synkrone nettserveren.

## Verifikasjon og vidare bygging

Kompilering bestod med **Espressif Arduino-ESP32 3.3.12**, kortprofil `esp32:esp32:esp32cam` og alle kompilatoråtvaringar aktiverte. Ingen åtvaringar blei rapporterte. Programmet brukar 1 029 593 byte av 3 145 728 byte app-plass. Globale variablar brukar 59 344 byte; dette omfattar ikkje allokeringar som blir gjorde under køyring.

Ti vertsbaserte logikktestar og fire nettgrensesnittstestar bestod. Testane brukar dei faktiske funksjonane frå skissa med simulert kamera/GPIO, og kontrollerer mellom anna biletkopiering før kamerabufferen blir returnert, avvising av for store/null-bilete, avprelling, eitt bilete ved halden knapp og nullstilling av nettgrensesnittet. Dei erstattar ikkje fysisk testing.

Sjå `../verification/firmware-r02.json` for kva som faktisk er kontrollert. Ingen fysisk ESP32-CAM er kopla til denne arbeidsøkta. Programmet er ikkje flashet eller funksjonstesta på brukaren sitt utstyr. Passform, kamerafleks, faktisk brytarhøgd/retur og straumforsyning må prøvast fysisk før huset blir lukka.

For innbygging: oppnå først bilete på benken, deretter fungerande knapp, deretter prøvepass i open kamerahaldar. Hald straumen fråkopla under mekanisk montering. Bekreft at USB-plugg og leidningar går fritt før baklokket blir låst.

## Primærgrunnlag

- [Espressif: installasjon av Arduino-ESP32](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html)
- [Espressif: AI Thinker-kamerapinnar i offisielt eksempel](https://github.com/espressif/arduino-esp32/blob/master/libraries/ESP32/examples/Camera/CameraWebServer/camera_pins.h)
- [Espressif: offisiell kamerainitialisering](https://github.com/espressif/arduino-esp32/blob/master/libraries/ESP32/examples/Camera/CameraWebServer/CameraWebServer.ino)
- [Espressif: synkron WebServer](https://github.com/espressif/arduino-esp32/blob/master/libraries/WebServer/src/WebServer.h)
- [Espressif: Wi-Fi AP](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/wifi.html)
- [Espressif: GPIO og INPUT_PULLUP](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/gpio.html)
- [Espressif: oppstartsmodus](https://docs.espressif.com/projects/esptool/en/latest/esp32/advanced-topics/boot-mode-selection.html)
- [Olimex: ESP32-CAM-MB-skjema](https://www.olimex.com/Products/IoT/ESP32/ESP32-CAM/resources/ESP32-CAM-MB-S001.jpg)

Pinnekartet følgjer AI Thinker-varianten: PWDN32, RESET-1, XCLK0, SCCB26/27, D0-D7 = 5/18/19/21/36/39/34/35, VSYNC25, HREF23, PCLK22. Dette er ikkje eit universelt kart for alle ESP32-kamerakort.
