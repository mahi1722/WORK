$ErrorActionPreference = 'Stop'
$result = [PSCustomObject]@{
    Status        = ""
    OutputMessage = ""
    ErrorMessage  = ""
}
try
{
    $SecurityGroup = $ADDITIONAL_VARIABLES.uniquegroupname
    if(Get-ADGroup -Identity "$SecurityGroup"){
        $result.OutputMessage = "Automation has validated that the security group "+ $SecurityGroup + " already exist in AD"
        $result.Status = "Failed" 
}
}catch
{
    if($_.CategoryInfo.Reason -eq "ADIdentityNotFoundException")
    {
        $result.OutputMessage = "Automation has validated that the security group "+ $SecurityGroup + " does not exist in AD"
        $result.Status = "Success"
    }
    else
    {
        $result.ErrorMessage = "ErrorCode: "+$_.Exception.Message
        $result.Status = "Error"
    }
            
}

$result = $result | ConvertTo-Json
$result