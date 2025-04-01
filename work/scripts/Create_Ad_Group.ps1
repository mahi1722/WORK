$ErrorActionPreference = 'Stop'
$result = [pscustomobject]@{
    Status        = ""
    OutputMessage = ""
    ErrorMessage  = ""
}

try
{

    $Group = $ADDITIONAL_VARIABLES.uniquegroupname
    $manager = $ADDITIONAL_VARIABLES.OwnerSamAccount
    $description = $ADDITIONAL_VARIABLES.Purposeofthegroup

    New-ADGroup -Name "$Group" -GroupCategory Security -GroupScope Global -ManagedBy $manager -Description $description;
    $ADGroup = (Get-ADGroup -Filter 'SamAccountName -eq $Group').SamAccountName
    if ($ADGroup -ne $null)
    {
    $result.OutputMessage = "Automation successfully created security group "+$Group+" in AD"
    $result.Status = "Success"
    }else{
    $result.OutputMessage = "Automation has failed to create security group "+$Group+" in AD"
    $result.Status = "Error"
    }      
}
catch
{
        $result.ErrorMessage= "ErrorCode: "+$_.Exception.Message
        $result.Status = "Error"
}

$result = $result | ConvertTo-Json

$result
