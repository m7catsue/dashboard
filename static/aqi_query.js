var dialog = $( "#dialog" );                          //JQueryUI弹窗,用于展示AQI查询结果

$(function () {
  $( "#dialog" ).dialog({
    autoOpen: false
  });

  $("#submit").click(function() {
    $("#dialog").dialog('open');
  });
});

var mapping = {
    'beijing': '北京',
    'chengdu': '成都',
    'chongqing': '重庆',
    'guangzhou': '广州',
    'shanghai': '上海',
    'shenyang': '沈阳'
};

function getAqiLevel(aqi_value) {
    if (0<aqi_value && aqi_value<=50) {             //注意javascript比较数值大小的格式
        return '优'
    } else if (50<aqi_value && aqi_value<=100) {
        return '良'
    } else if (100<aqi_value && aqi_value<=150) {
        return '轻度污染'
    } else if (150<aqi_value && aqi_value<=200) {
        return '中度污染'
    } else if (200<aqi_value && aqi_value<=300) {
        return '重度污染'
    } else {
        return '严重污染'
    }
}

function aqiQuery() {
    var selected_city = $("select#selected-city").val();
    var token = '87711e84f75008ae850fde4a59410486da3b8585';
    var query_url = 'http://api.waqi.info/feed/' + selected_city +'/?token=87711e84f75008ae850fde4a59410486da3b8585';
    $.ajax(query_url, {
        async: true,
        method: 'GET',
        dataType: 'json'
    }).done(function (data) {
        var status = data.status;
        console.log(status);
        if (status==='ok') {
            var aqi_value = data.data.aqi;
            var aqi_level = getAqiLevel(aqi_value);
            var updated_time = data.data.time.s;
            alert('城市: ' + mapping[selected_city] + ', 空气质量指数(AQI): ' + aqi_value + ', 空气质量等级: ' + aqi_level +
            '; 最后更新时间: ' + updated_time + '.');
        } else {
            var error = data.data;
            alert('AQI查询失败，原因: ' + error)
        }
    }).fail(function (xhr, status) {
        alert('AQI查询失败，请稍后重试。');
    }).always(function () {
        alert('请不要过于频繁使用AQI实时查询功能，过于频繁的API请求可能会导致密匙被API提供者收回。' +
              '该数据每小时更新。');
    });
}




