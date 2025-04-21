@echo off
set zipfile=lambda_function.zip

if exist "%cd%\%zipfile%" (
    echo O item existe. Deletando...
    del /f /q "%cd%\%zipfile%"
    echo Arquivo deletado com sucesso.
) else (
    echo O item nao existe.
)

powershell Compress-Archive -Path "%cd%\src\*" -DestinationPath "%cd%\%zipfile%"
echo Arquivos zipados com sucesso!

pause