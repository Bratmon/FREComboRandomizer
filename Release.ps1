pyinstaller -F .\Python\shuffle.py

Copy-Item .\dist\shuffle.exe .\Release\lib\shuffle.exe

Copy-Item '.\Combo Randomizer.lua' '.\Release\Combo Randomizer.lua'
Copy-Item .\memory.lua .\Release\lib\memory.lua
Copy-Item .\ips.lua .\Release\lib\ips.lua

Copy-Item -Path .\savestate_templates\* .\Release\lib\savestate_templates\ -Recurse
Copy-Item -Path  '.\Patches\Emerald Patch.ips' '.\Release\lib\Patches\Pokemon - Emerald Version (U).gba.ips' -Recurse
Copy-Item -Path  '.\Patches\Fire Red 11 Patch.ips' '.\Release\lib\Patches\Pokemon - Fire Red Version (U) (V1.1).gba.ips' -Recurse
Copy-Item -Path .\hubs\* .\Release\lib\hubs\ -Recurse -Force
