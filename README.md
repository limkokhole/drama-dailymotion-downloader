# drama-dailymotion-downloader
擁有 dailymotion 的 drama/連續劇網站下載器  

複製鏈接，然後自定義下載第幾集的i連續劇視頻, 適用於 https://dramaq.de/ 和 https://journalflash.com/ 之類擁有 Dailymotion 源的網站。除了主題，也可以下載其它網站視頻例如 YouTube。

#### 圖形界面:
Windows-64 bit 用戶可以下載 "win 64 dailymotion drama 連續劇下載器.zip", 解壓縮後， 雙擊 "dailymotion 連續劇下載器.exe" 文件執行。請確保附件 ffmpeg 在同一個目錄。 

命令行愛好者也可以 python drama_dailymotion_gui.py 打開。

#### 命令行界面:
請自行參考 `python drama_dailymotion_console.py --help`。

例子1: python3 drama_dailymotion_console.py https://dramaq.de/cn191023b --from-ep 1 -to-ep 5  
例子2: python3 drama_dailymotion_console.py https://journalflash.com/cn191023b/18.html#3 --from-ep 36 -to-ep 36  
例子3: python3 drama_dailymotion_console.py https://www.youtube.com/watch?v=H_nL7WOehhQ -any  

#### 注意事項:

1. 開始下載時每集會出現黑窗口幾秒。
2. 可能要暫時停止才能看到文件大小更新。放心， 正常情況下可以繼續下載剩下的， 不會從零開始。
3. 由於可能是 4K， 所以請確保硬盤有足夠的容量。

#### 示範視頻 (點擊圖片會在 YouTube 打開):

[![watch in youtube](https://i.ytimg.com/vi/xxx/hqdefault.jpg)](https://www.youtube.com/watch?v=xxx "獨播庫下載器")
