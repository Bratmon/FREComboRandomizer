pyinstaller -F .\Python\shuffle.py
pyinstaller -F .\Python\ips.py

Copy-Item .\dist\shuffle.exe .\Release\lib\shuffle.exe
Copy-Item .\dist\ips.exe .\Release\lib\ips.exe

Copy-Item '.\Combo Randomizer.lua' '.\Release\Combo Randomizer.lua'
Copy-Item .\memory.lua .\Release\lib\memory.lua

Copy-Item -Path .\savestate_templates\* .\Release\lib\savestate_templates\ -Recurse
Copy-Item -Path .\Patches\* .\Release\lib\Patches\ -Recurse
Copy-Item -Path .\hubs\* .\Release\lib\hubs\ -Recurse -Force
