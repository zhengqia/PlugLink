/**
 * 界面入口模块  
 */
 
layui.define('admin', function(exports){
  var setter = layui.setter;
  var element = layui.element;
  var admin = layui.admin;
  var tabsPage = admin.tabsPage;
  var view = layui.view;
  var util = layui.util;
  
  // 打开标签页
  var openTabsPage = function(options){
    options = $.extend({
      url: '',
      escape: true
    }, options);

    // 遍历页签选项卡
    var matchTo;
    var tabs = $('#LAY_app_tabsheader>li');
    var path = options.url.replace(/(^http(s*):)|(\?[\s\S]*$)/g, '');
    
    tabs.each(function(index){
      var li = $(this);
      var layid = li.attr('lay-id');
      
      if(layid === options.url){
        matchTo = true;
        tabsPage.index = index;
      }
    });

    options.title = options.title || (tabsPage.index === 0 ? '' : '新标签页');
    
    // 定位当前 tabs
    var setThisTab = function(){
      element.tabChange(FILTER_TAB_TBAS, options.url);

      admin.tabsBodyChange(tabsPage.index, {
        url: options.url,
        title: options.title
      });
    };
    
    if(setter.pageTabs){
      // 如果未在选项卡中匹配到，则追加选项卡
      if(!matchTo){
        // 延迟修复 Firefox 空白问题
        setTimeout(function(){
          $(APP_BODY).append([
            '<div class="layadmin-tabsbody-item layui-show">'
              ,'<iframe src="'+ options.url +'" frameborder="0" class="layadmin-iframe"></iframe>'
            ,'</div>'
          ].join(''));
          setThisTab();
        }, 10);
        
        tabsPage.index = tabs.length;
        element.tabAdd(FILTER_TAB_TBAS, {
          title: '<span>'+ function(title){
            return options.highlight 
              ? '<span style="'+ options.highlight +'">'+ title +'</span>' 
            : title;
          }(util.escape(options.title)) +'</span>',
          id: options.url,
          attr: path
        });
        
      }
    } else {
      var iframe = admin.tabsBody(admin.tabsPage.index).find('.layadmin-iframe');
      iframe[0].contentWindow.location.href = options.url;
    }

    // 执行定位当前 tabs
    setThisTab();
  };
  
  var APP_BODY = '#LAY_app_body';
  var FILTER_TAB_TBAS = 'layadmin-layout-tabs';
  var $ = layui.$;
  var $win = $(window);
  
  //初始
  if(admin.screen() < 2) admin.sideFlexible();
  
  view().autoRender();

  // 根据 record 属性，打开对应的初始页面
  var openInitPage = (function fn(){
    var url = layui.url();
    var hash = url.hash;
    var record = setter.record || {};
    var url = hash.path.join('/');
    var title = function(){
      var dataRecord = layui.data(setter.tableName).record || {};
      return dataRecord[url] || '';
    }();

    (function(){
      if(!record.url) return;
      if(url){
        // 禁止读取远程 url
        if(function(url){
          return /^(\w*:)*\/\/.+/.test(url) && url.indexOf(location.hostname) === -1
        }($.trim(url))) return fn;

        openTabsPage({
          url: url,
          title: title
        });
      }
    })();

    setTimeout(function(){
      $('#'+ setter.container).css('visibility', 'visible');
    }, 300);

    return fn;
  })();

  // 对外输出
  var adminuiIndex = {
    openTabsPage: openTabsPage
  };

  $.extend(admin, adminuiIndex);
  exports('adminIndex', adminuiIndex);
});
