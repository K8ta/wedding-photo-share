function dojQueryAjax() {
 
    // jQueryのajaxメソッドを使用しajax通信
    $.ajax({
        type: "GET", 
        url: "ajax",
        cache: true,
        // 通信成功時に呼び出されるコールバック
        success: function (data) {
            if(data == ""){
                window.location.href = "ranking";
            }else{
                $('.height').html(data);
            }
        },
    });
}
 
window.addEventListener('load', function () {
    setTimeout(dojQueryAjax, 0);
    setInterval(function() {
      if(!isPaused) {
        dojQueryAjax()
      }
    // インターバル7秒
    }, 7000);
});