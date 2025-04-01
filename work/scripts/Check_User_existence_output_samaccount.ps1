$ErrorActionPreference = 'STOP'
$result = [PSCustomObject]@{
    Status         = ""
    OutputMessage  = ""
    ErrorMessage   = ""
    SamAccountName = ""
}
try{   
    $upn = $ADDITIONAL_VARIABLES.Userstobeadded
    
    $user = (Get-ADUser -Filter{UserPrincipalName -eq $upn})
    if($user)
    {
        $result.OutputMessage = "Automation has validated that the user "+$upn+" exist in AD"
		$result.Status = "Success"
        $result.SamAccountName = $user.SamAccountName
    }
    else
    {
        $result.OutputMessage = "Automation has validated that the user "+$upn+" not exist in AD"
        $result.Status = "Error"
    }
}catch
{
    $result.ErrorMessage= "ErrorCode: "+$_.Exception.Message
    $result.Status = "Error"
            
}

$result = $result | ConvertTo-Json

$result
