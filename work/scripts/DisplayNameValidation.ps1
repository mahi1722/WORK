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
			DisplayName = ""
			OU = ""
			Status = ""
			errcode = ""
		}

	do
	{
		Try
		{
		   $chekupn = Get-ADUser -Filter "DisplayName -eq '$DisplayName'" -Credential $Credential
		   if($chekupn)
		   {
				$DispCreation = 'Attempting'
				$digicheck = check-digits -inputstring $DisplayName
				if($digicheck.charlength -eq 0)
				{
					$DisplayName = $DisplayName + $j
				}
				else
				{
					[int]$digpart = $digicheck.value
					$DisplayName = $DisplayName.Substring(0,$DisplayName.Length-$digicheck.charlength) +  ($digpart+ $j)
				}
		   }
		   else
		   {
				$DispCreation = "Success"
		   }
		}
		catch
		{
			$Errorvar = "True"
			$finalobj.Status = "Failed"
			$finalobj.errcode = "ErrorCode:" + $_.exception.message
			$finalobj | ConvertTo-Json
			Exit
		}
	}
	while($DispCreation -eq "Attempting" -and $Errorvar -eq "False")
	$finalobj.Status = "Success"
	$finalobj.DisplayName = $DisplayName
	$finalobj | ConvertTo-Json
	
   
}
catch
{
   			 		
			 "ErrorCode:" + $_.exception.message
}
		
$result = $result | ConvertTo-Json
$result