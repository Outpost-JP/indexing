
document.getElementById('urlForm').addEventListener('submit', function(event) {
    event.preventDefault(); // フォームの自動送信を防止
    const url = document.getElementById('urlInput').value; // 入力されたURLを取得

    // 確認アラートを表示
    const isConfirmed = confirm('本当に送信しますか？');

    if (isConfirmed) {
        // ここでフォーム送信のロジックを実装できます
        // 例: console.log(url); またはサーバーへの送信など
        alert('送信されました: ' + url);
    }
});
