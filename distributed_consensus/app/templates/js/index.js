$(function(){
  init();
})

function init(){
  initTab();
  initEvent();
  initChart();
}

function initTab(){
  var config = $("#config-tab");
  var active_bar_bottom = config.find(".active-bar-bottom");
  var active_bar_top = config.find(".active-bar-top");
  var active_bt = config.find(".tab-bt.active");
  var left = active_bt.position().left;
  var width = active_bt.css('width');
  active_bar_bottom.css('width',width);
  active_bar_bottom.css("transform","translateX("+left+"px)")
  active_bar_top.css('width',width);
  active_bar_top.css("transform","translateX("+left+"px)")


  var target = active_bt.attr('target');
  var panel = config.find('.tab-content>div[name="'+target+'"]');
  panel.siblings().hide();
  panel.show();
}

function initEvent(){
  $("#config-tab").on('click',".tab-bt",function(e){
    $(this).addClass('active');
    $(this).siblings().removeClass('active');
    initTab();
  });

}

function initChart(){
  var myChart = echarts.init(document.getElementById('pchart'));
  option = {
    xAxis: {
        type: 'category',
        data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    },
    yAxis: {
        type: 'value'
    },
    series: [{
        data: [820, 932, 901, 934, 1290, 1330, 1320],
        type: 'line',
        smooth: true
    }]
  };
  myChart.setOption(option);
}