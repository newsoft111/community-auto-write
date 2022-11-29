<?php
include "dbcon.php";


if ($_SERVER['REQUEST_METHOD'] == 'POST') {
	$id = StrToLower($_POST['id']);
	$pw = StrToLower($_POST['pw']);
	$sql = "SELECT * FROM user WHERE username='{$id}'";
	$result = $connect->query($sql);
	if ($result->num_rows < 1) {
		$arr = array("error"=>"아이디 또는 비밀번호를 확인해주세요.");
		echo returnJson($arr);
		Exit;
	} else {
		$row = $result->fetch_array();
		$now = strtotime(date("Y-m-d"));
		$expires_at = strtotime($row['expires_at']);

		if ($pw == $row['password']) {
			if ($now > $expires_at) {
				$arr = array("error"=>"기간이 만료되었습니다.");
				echo returnJson($arr);
				Exit;
			}
			$session = md5(rand());
			SetCookie('AuthId',$id,-1,'/');
			SetCookie('AuthSession',$session,-1,'/');
			$sql = "UPDATE user SET session='$session' WHERE username='$id'";
			$connect->query($sql);
		
			$arr = array("session"=>$session, "expires_at"=>$row['expires_at'], "limit_site"=>$row['limit_site'], "error"=>"0");

			$sql = "SELECT * FROM version limit 0,1";
			$result = $connect->query($sql);
			$row = $result->fetch_array();

			$arr["version"] = $row["version"];

			echo returnJson($arr);
		} else {
			$arr = array("error"=>"아이디 또는 비밀번호를 확인해주세요.");
			echo returnJson($arr);
			Exit;
		}
	}
} else {
	echo getSession($connect);
}

$connect->close();

function getSession($connect) {
	$AuthId = addslashes($_COOKIE['AuthId']);
	$AuthSession = addslashes($_COOKIE['AuthSession']);

	$sql = "SELECT * FROM user WHERE username='$AuthId'";
	$result = $connect->query($sql);
	$row = $result->fetch_array();

	$now = strtotime(date("Y-m-d"));
	$expires_at = strtotime($row['expires_at']);

		
	if ($AuthId && $AuthSession) {
		if ($row['session'] != $AuthSession) {
			SetCookie('AuthId','',0,'/');
			SetCookie('AuthSession','',0,'/');
		}
	}
	if ($now > $expires_at) {
		SetCookie('AuthId','',0,'/');
		SetCookie('AuthSession','',0,'/');
	}
	$arr = array("session"=>$row['session'], "expires_at"=>$row['expires_at'], "limit_site"=>$row['limit_site'], "error"=>"0");
	$sql = "SELECT * FROM version limit 0,1";
	$result = $connect->query($sql);
	$row = $result->fetch_array();

	$arr["version"] = $row["version"];

	header('Content-Type: application/json');
	return json_encode($arr, JSON_PRETTY_PRINT);
}

function returnJson($arr) {
	header('Content-Type: application/json');
	echo json_encode($arr, JSON_PRETTY_PRINT);
}
?>