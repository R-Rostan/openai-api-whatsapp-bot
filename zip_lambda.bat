@echo off
set zipfile=messages.zip

if exist "%cd%\%zipfile%" (
    echo O item existe. Deletando...
    del /f /q "%cd%\%zipfile%"
    echo Arquivo deletado com sucesso.
) else (
    echo O item nao existe.
)

powershell Compress-Archive -Path "%cd%\src\messages\*" -DestinationPath "%cd%\%zipfile%"
echo Arquivos zipados com sucesso!

pause