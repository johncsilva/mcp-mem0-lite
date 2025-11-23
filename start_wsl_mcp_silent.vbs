' Script VBS para iniciar o servidor MCP no WSL silenciosamente
' Executa o script .bat sem mostrar janela

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Obtém o diretório do script
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Caminho do batch file
batFile = scriptDir & "\start_wsl_mcp.bat"

' Executa o batch em modo oculto (0 = janela oculta, True = esperar conclusão)
WshShell.Run Chr(34) & batFile & Chr(34), 0, True

Set WshShell = Nothing
Set fso = Nothing
