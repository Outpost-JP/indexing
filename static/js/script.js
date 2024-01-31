document.getElementById('urlForm').addEventListener('submit', function(event) {
    event.preventDefault(); // フォームの自動送信を防止
    const firstUrlInput = document.getElementById('firstUrlInput').value; // 最初のURLを取得
    const lastUrlInput = document.getElementById('lastUrlInput').value; // 最後のURLを取得

    // 確認アラートを表示
    const isConfirmed = confirm('本当に送信しますか？');

    if (isConfirmed) {
        // XMLHttpRequestを使用してサーバーにPOSTリクエストを送信
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/process', true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

        xhr.onreadystatechange = function() {
            if (this.readyState === XMLHttpRequest.DONE) {
                if (this.status === 200) {
                    // 処理結果をページに表示
                    document.getElementById('result').innerHTML = this.responseText;
                } else {
                    // エラーが発生した場合
                    document.getElementById('result').innerHTML = 'エラーが発生しました: ステータスコード ' + this.status;
                }
            }
        };

        // 正しいキーを使用してデータをエンコード
        const data = `firstUrlInput=${encodeURIComponent(firstUrlInput)}&lastUrlInput=${encodeURIComponent(lastUrlInput)}`;
        xhr.send(data);
    }
});
