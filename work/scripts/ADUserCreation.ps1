
$ErrorActionPreference = 'STOP'

$result = [PSCustomObject]@{
    Status        = ""
    OutputMessage = ""
    ErrorMessage  = ""
}

try{
$password=ConvertTo-SecureString $ADpassword -AsPlainText -Force
$Credential=New-Object System.Management.Automation.PSCredential ($ADusername, $password)

    #Import-Module ActiveDirectory;
       	New-ADUser -SamAccountName $SamAccountName -UserPrincipalName $UserPrincipalName -Name $Name -GivenName $FirstName -Surname $LastName -Enabled $True -ChangePasswordAtLogon $True -DisplayName $DisplayName -Department $Department -Path $OU -Title $JobTitle -Manager $Manager -AccountPassword (convertto-securestring $DefaultPassword -AsPlainText -Force) -Description $Description -Office $UserLocation -Credential $Credential;
  
       	  
			if($?)
			{
			$Exitcode = "User Created Successfully"
			}else
			{
			$Exitcode = "ErrorCode: User is not Created"
			}
        $Exitcode
            
    } 
     

Catch {           
        $Exitcode = 'ErrorCode: ' + $_.exception.Message
        $Exitcode
        Clear-Variable Exitcode 
        exit         
}



$result = $result | ConvertTo-Json
$result