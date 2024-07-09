package main

// func testNotify() {
// 	for {
// 		time.Sleep(2 * time.Second)
// 		msg := `{"accounts":{"nn2":[false,25,6418,6418]},"command":"NOTIFY_GAME_TERMINATED","lobby_id":"a224af83b68748544cded000a961d2cd119b05ac14080aa077b4898fe2bcc103","map_name":"tokio","request_id":"f8f52cf1a5089e50dd602d529e2a8cc7"}`
// 		server_api.NOTIFY_GAME_TERMINATED([]byte(msg), func(response []byte) {})
// 	}
// }

// func testUpdateAccountRanking() {
// 	time.Sleep(time.Second * 5)
// 	for {
// 		ranking.OnAccountUpdated(dict{
// 			"account_name":         "Test1",
// 			"display_name":         "RUCK",
// 			"player_readonly_data": `{"maps_data": {"tokio": [1000, 8000, 8000]} }`,
// 		})
// 	}
// }

// func testUpdateAccountRanking2() {
// 	time.Sleep(time.Second * 5)
// 	for {
// 		ranking.OnAccountUpdated(dict{
// 			"account_name":         "Test2",
// 			"display_name":         "RAS",
// 			"player_readonly_data": `{"maps_data": {"tokio": [10, 7300, 7300]} }`,
// 		})
// 	}
// }
