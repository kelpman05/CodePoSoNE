$(function(){
  init();
})
var state_time_span;
function init(){
  initWebSocket();
  initTab();
  initSelection();
  initEvent();
  //initChart();
}

function initWebSocket(){
  var host = window.location.host ;
  var socket = io.connect(host);
  socket.on('connect', function() {
    socket.emit('message','I\'m connected!');
  });
  // console消息
  socket.on('console', function (data) {
    var p=$("<p></p>").text(data)
    $("#console").append(p)
    var nScrollHight = $("#console")[0].scrollHeight
    //$("#console").animate({scrollTop:p.offset().top},1000);
    $("#console").scrollTop(nScrollHight);
  });
  // 当前价格变更
  socket.on('price', function (ep,gp,hp) {
    var tr = $("<tr></tr>");
    //tr.append($("<td></td>").text(Math.floor(ep*1000)/1000));
    //tr.append($("<td></td>").text(Math.floor(gp*1000)/1000));
    //tr.append($("<td></td>").text(Math.floor(hp*1000)/1000));
    tr.append($("<td></td>").text(ep));
    tr.append($("<td></td>").text(gp));
    tr.append($("<td></td>").text(hp));
    $("#price_body").html(tr);
  });
  var prices_time_span;
  socket.on('prices',function(data,time_span){
    if(prices_time_span&&time_span<prices_time_span){
      return;
    }
    $("#prices_body").html('');
    data.forEach(function(item,index){
        var tr = $("<tr></tr>");
        tr.append($("<td></td>").text(Math.floor(item[0]*1000)/1000));
        tr.append($("<td></td>").text(Math.floor(item[1]*1000)/1000));
        tr.append($("<td></td>").text(Math.floor(item[2]*1000)/1000));
        tr.append($("<td></td>").text(Math.floor(item[3]*1000)/1000));
        $("#prices_body").append(tr);
    })
    prices_time_span = time_span;
  })
  // 当前需求量变更
  socket.on('demand', function (ed,gd,hd) {
    var tr = $("<tr></tr>");
    //tr.append($("<td></td>").text(Math.floor(ed*1000)/1000));
    //tr.append($("<td></td>").text(Math.floor(gd*1000)/1000));
    //tr.append($("<td></td>").text(Math.floor(hd*1000)/1000));
    tr.append($("<td></td>").text(ed));
    tr.append($("<td></td>").text(gd));
    tr.append($("<td></td>").text(hd));
    $("#demand_body").html(tr);
  });
  var demands_time_span;
  var demands_timeout_handle;
  socket.on('demands',function(data,time_span){
    console.log(data);
    console.log(time_span);
    if(demands_time_span&&time_span<demands_time_span){
      return;
    }
    if(demands_timeout_handle){
      clearTimeout(demands_timeout_handle);
    }
    demands_timeout_handle = setTimeout(function(values){
      $("#demands_body").html('');
      values.forEach(function(item,index){
          var tr = $("<tr></tr>");
          tr.append($("<td></td>").text(Math.floor(item[0]*1000)/1000));
          tr.append($("<td></td>").text(Math.floor(item[1]*1000)/1000));
          tr.append($("<td></td>").text(Math.floor(item[2]*1000)/1000));
          tr.append($("<td></td>").text(Math.floor(item[3]*1000)/1000));
          $("#demands_body").append(tr);
      })
    },1000,data); 
    demands_time_span = time_span;
  })
  // 当前周期变更 
  socket.on('round', function (data) {
    $("#round").text(data);
  });
  socket.on('blacklist',function(data){
    $("#blacklist").text(data)
  });
  socket.on('state',function(running,running_mark){
    if(state_time_span&&running_mark<state_time_span){
      return;
    }
    state_time_span = running_mark;
    var bt_start = $("#bt_start");
    if(running){
      bt_start.attr('disabled','disabled');
      bt_start.siblings().removeAttr('disabled');
    }else{
      bt_start.siblings().attr('disabled','disabled');
      bt_start.removeAttr('disabled');
    }
  });
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

function initSelection(){
  $(".evil select").each(function(index,item){
    var placeholder=$(item).attr('placeholder');
    $(item).multipleSelect({
      　　　　addTitle: true, //鼠标点悬停在下拉框时是否显示被选中的值
      　　　　selectAll: false, //是否显示全部复选框，默认显示
      　　　　name: "质控级别",
      　　　　selectAllText: "选择全部", //选择全部的复选框的text值
      　　　　allSelected: "全部", //全部选中后显示的值
      　　　　//delimiter: ', ', //多个值直接的间隔符，默认是逗号
      　　　　placeholder: placeholder, //不选择时下拉框显示的内容
             minimumCountSelected:3,
             ellipsis:true
      　　});
  })
  
  $('#checkedLevel').multipleSelect('setSelects', [1,2,4]);
}

function initEvent(){
  $("#config-tab").on('click',".tab-bt",function(e){
    $(this).addClass('active');
    $(this).siblings().removeClass('active');
    initTab();
  });
  $("#config-tab").on('click',".bt-edit",function(e){
    showEdit(this);
  });
  $("#config-tab").on('click',".bt-sure",function(e){
    saveEdit(this);
  });
  $("#config-tab").on('click',".bt-cancel",function(e){
    cancelEdit(this);
  });
  $("#bt_start").on('click',function(e){
    start_bootstrap(this);
  });
  $("#bt_pause").on('click',function(e){
    stop_bootstrap(this);
  })
}


function start_bootstrap(e){
  $.ajax({
    url:'/running/start',
    type:"post",
    success:function(data){
      if(state_time_span&&data.time_span<state_time_span){
        return;
      }
      state_time_span = data.time_span;
      $(e).attr('disabled','disabled');
      $(e).siblings().removeAttr('disabled');
    }
  });
}

function stop_bootstrap(e){
  $.ajax({
    url:'/running/stop',
    type:"post",
    success:function(data){
      if(state_time_span&&data.time_span<state_time_span){
        return;
      }
      state_time_span = data.time_span;
      $(e).attr('disabled','disabled');
      $(e).siblings().removeAttr('disabled');
    }
  });
}

var forms_data = {}

function showEdit(e){
  $(e).css('display','none');
  var form = $(e).parents('form');
  var form_id = form[0].id;
  var form_values ={};
  form.find('.bt-editing').css('display','block');
  form.find('select.ms-item').each(function(index,item){
    //$(item).multipleSelect('enable')
    //插件原来的方法异常，可能是因为html结构发生过更改
    var item_id = item.id;
    var choice = $(item).siblings().find('.ms-choice');
    choice.removeClass('disabled');
    var selections = $(item).multipleSelect('getSelects');
    form_values[item_id] = selections;
  })
  form.find('.input-item').each(function(index,item){
    var item_id = item.id;
    var item_value = $(item).val();
    form_values[item_id] = item_value;
    $(item).removeAttr('disabled');
  });

  forms_data[form_id] = form_values;
}


function cacheForm(){

}

function resetForm(){

}

function saveEdit(e){
  var form = $(e).parents('form');
  var action = form[0].action;
  //var formdata = new FormData(form[0]);
  var formdata = getFormData(form);
  $.ajax({
    url:action,
    type:"post",
    data:formdata,
    processData:false,
    contentType:false,
    success:function(data){
        closeEdit(form);
    }
  });

}

function getFormData(form){
  var formdata = new FormData();
  form.find('select.ms-item').each(function(index,item){
    //$(item).multipleSelect('enable')
    //插件原来的方法异常，可能是因为html结构发生过更改
    var item_name = item.name;
    var selections = $(item).multipleSelect('getSelects');
    formdata.append(item_name,selections.join(','));
  })
  form.find('.input-item').each(function(index,item){
    var item_name = item.name;
    var item_value =$(item).val();
    formdata.append(item_name,item_value);
  });
  return formdata;
}

function closeEdit(form){
  form.find('.bt-editing').css('display','none');
  form.find('.bt-edit').css('display','block');
  form.find('select.ms-item').each(function(index,item){
    //$(item).multipleSelect('enable')
    //插件原来的方法异常，可能是因为html结构发生过更改
    var choice = $(item).siblings().find('.ms-choice');
    choice.addClass('disabled');
  })
  form.find('.input-item').attr('disabled','disabled');
  //ajax
  
}

function cancelEdit(e) {
  var form = $(e).parents('form');
  var form_id = form[0].id;
  var form_values = forms_data[form_id];
  form.find('.bt-editing').css('display','none');
  form.find('.bt-edit').css('display','block');
  form.find('select.ms-item').each(function(index,item){
    //$(item).multipleSelect('enable')
    //插件原来的方法异常，可能是因为html结构发生过更改
    var item_id = item.id;
    var choice = $(item).siblings().find('.ms-choice');
    choice.addClass('disabled');
    var selections = form_values[item_id];
    $(item).multipleSelect('setSelects', selections);
  })
  form.find('.input-item').each(function(index,item){
    var item_id = item.id;
    var item_value =form_values[item_id];
    $(item).val(item_value);
    $(item).attr('disabled','disabled');
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