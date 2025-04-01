$ErrorActionPreference = 'STOP'
$result = [PSCustomObject]@{
    Status         = ""
    OutputMessage  = ""
    ErrorMessage   = ""
}
try{   
    
    $User = $ADDITIONAL_VARIABLES.SamAccountName
    $Group = $ADDITIONAL_VARIABLES.uniquegroupname
    
    Add-ADGroupMember $Group -Members $User.trim()
    if($?)
    {
        $result.OutputMessage = "Automation has successfully addded the user "+ $upn + " to "+$Group+" security group`nHence closing the ticket"
		$result.Status = "Success"
    }
    else
    {
        $result.OutputMessage = "Automation has failed to add the user "+ $upn+" to "+$Group+" security group"
        $result.Status = "Error"
    }
}catch
{
    $result.ErrorMessage= "ErrorCode: "+$_.Exception.Message
    $result.Status = "Error"
            
}

$result = $result | ConvertTo-Json

$result