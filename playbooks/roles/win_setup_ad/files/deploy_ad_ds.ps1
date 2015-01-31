#
# Windows PowerShell script for AD DS Deployment
#

Param(
    [string]$safeModeAdministratorPassword = "S3tM3Pl3as3!",
    [string]$domainName = "ansible.local",
    [string]$netbiosName = "ANSIBLE"
)

$ErrorActionPreference = "Stop"
trap
{
    Write-Host $_
    Exit 1
}

try
{
    $ad_dc = Get-ADDomainController
    Write-Host $ad_dc.Domain
}
catch
{
    $smap = ConvertTo-SecureString $safeModeAdministratorPassword -AsPlainText -Force
    Import-Module ADDSDeployment
    Install-ADDSForest `
        -DomainMode "Win2008" `
        -DomainName $domainName `
        -DomainNetbiosName $netbiosName `
        -ForestMode "Win2008" `
        -InstallDns:$true `
        -Force:$true `
        -SafeModeAdministratorPassword $smap
}
