jQuery(document).ready(function($) {
    //避免出现错误: $(.).dialog is not a function,
    //将所有JS代码放入ready函数block(确保JQuery已完全加载)
    console.log('JQuery loaded.');
    var mapping = {
        'beijing': '北京',
        'chengdu': '成都',
        'chongqing': '重庆',
        'guangzhou': '广州',
        'shanghai': '上海',
        'shenyang': '沈阳'
    };

    function getAqiLevel(aqi_value) {
        if (0<aqi_value && aqi_value<=50) {          //javascript比较数值大小的格式
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

    $(function () {
      $( "#dialog" ).dialog({                        //初始化dialog;设置相关属性
        autoOpen: false,
        width: 400,
        height: 150,
        resizable: false,
        position: { my: 'top', at: 'top+80' },
        show: {
            effect: "slide",
            duration: 180
        },
        hide: {
        effect: "slide",
        duration: 180
        }
      });

      $("#submit").click(function() {                //点击submit后执行回调函数(进行ajax请求)
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
                var message = '城市: ' + mapping[selected_city] + ', 空气质量指数(AQI): ' + aqi_value + ', 空气质量等级: ' + aqi_level +
                '; 最后更新时间: ' + updated_time + '.';
                $('div#dialog>p').text(message);
            } else {
                var error = data.data;
                var message = 'AQI查询失败，原因: ' + error;
                $('div#dialog>p').text(message);
            }
        }).fail(function (xhr, status) {
            var message = 'AQI查询失败，请稍后重试。';
            $('div#dialog>p').text(message);
        });

        $("#dialog").dialog('open');
      });
    });

});

