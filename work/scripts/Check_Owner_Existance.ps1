$ErrorActionPreference = 'STOP'
$result = [PSCustomObject]@{
    Status          = ""
    OutputMessage   = ""
    ErrorMessage    = ""
    OwnerSamAccount = ""
}
try{   
    $upn = $ADDITIONAL_VARIABLES.OwnerEmail
    
    $user = (Get-ADUser -Filter{UserPrincipalName -eq $upn})
    if($user)
    {
        $result.OutputMessage = "Automation has validated that the Owner "+ $upn +" exists in AD"
		$result.Status = "Success"
        $result.OwnerSamAccount = $user.SamAccountName
    }
    else
    {
        $result.OutputMessage = "Automation has validated that the Owner "+ $upn +" not exists in AD"
        $result.Status = "Error"
    }
}catch
{
    $result.ErrorMessage= "ErrorCode: "+$_.Exception.Message
    $result.Status = "Error"
            
}

$result = $result | ConvertTo-Json

$result
