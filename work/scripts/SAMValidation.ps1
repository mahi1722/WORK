$ErrorActionPreference = 'Stop'
$result = [PSCustomObject]@{
    Status        = ""
    OutputMessage = ""
    ErrorMessage  = ""
}


try{
$password=ConvertTo-SecureString $ADpassword -AsPlainText -Force
$Credential=New-Object System.Management.Automation.PSCredential ($ADusername, $password)
 
    Function check-digits{
        [CmdletBinding()]
        param(
            [Parameter(Mandatory=$true)]
            [string]$inputstring
        )
        [int]$i = 1
        $outobj = [pscustomobject]@{
            value = ""
            charlength = ""
        }
        Do
        {
            $neededchar = $inputstring.Substring($inputstring.Length-$i)
            if($neededchar -as [int])
            {
                $check = "True"
                $i++
            }
            else
            {
                $check = "False"
            }
        }
        while($check -eq "True")
        $outobj.value = $inputstring.Substring($inputstring.Length-($i-1))
        $outobj.charlength = $i-1
        $outobj
    }
		$Errorvar = "False"
		[int]$j = 1
		$finalobj = [pscustomobject]@{
            SamAccountName = ""
            Status = ""
            
        }
    do
    {
        Try
        {
            $Checksam = Get-ADUser -Filter "SamAccountName -eq '$SamAccountName'" -Credential $Credential
            if($checksam)
            {
                $SamAccountNameCreation = 'Attempting'
                $digicheck = check-digits -inputstring $SamAccountName
                if($digicheck.charlength -eq 0)
                {
                    $SamAccountName = $SamAccountName + $j                
                }
                else
                {
                    [int]$digpart = $digicheck.value
                    $SamAccountName = $SamAccountName.Substring(0,$SamAccountName.Length-$digicheck.charlength) +  ($digpart+ $j)              
                }
            }
            else
            {
                $SamAccountNameCreation = "Success"
                $finalobj.Status = "Success"
                $finalobj.SamAccountName = $SamAccountName
                
            }
        }
        catch
        {
            $Errorvar = "True"
            $finalobj.Status = "Failed"
             "ErrorCode:"+ $_.exception.message     
        }
    }
    while($SamAccountNameCreation -eq "Attempting" -and $Errorvar -eq "False")
    $finalobj | ConvertTo-Json;
    


}
Catch {           
       'ErrorCode:' + $_.exception.Message
             
}

$result = $result | ConvertTo-Json
$result