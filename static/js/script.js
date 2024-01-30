document.getElementById('urlForm').addEventListener('submit', function(event) {
    event.preventDefault(); // フォームの自動送信を防止
    const url = document.getElementById('urlInput').value; // 入力されたURLを取得

    // 確認アラートを表示
    const isConfirmed = confirm('本当に送信しますか？');

    if (isConfirmed) {
        // XMLHttpRequestを使用してサーバーにPOSTリクエストを送信
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/process', true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

        xhr.onreadystatechange = function() {
            if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                // レスポンスが返ってきたときの処理をここに書く
                alert('サーバーが応答しました: ' + this.responseText);
            }
        };

        // リクエストの本文にデータを設定して送信
        xhr.send('input=' + encodeURIComponent(url));
    }
});
