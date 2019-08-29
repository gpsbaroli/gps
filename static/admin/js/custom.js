(function($) {
    'use strict';


    function getQueryStrings(query_string) {
        var assoc  = {};
        var decode = function (s) { return decodeURIComponent(s.replace(/\+/g, " ")); };
        var queryString = location.search.substring(1); 
        var keyValues = queryString.split('&'); 
      
        for(var i in keyValues) { 
          var key = keyValues[i].split('=');
          if (key.length > 1) {
            assoc[decode(key[0])] = decode(key[1]);
          }
        }     
        return assoc[query_string]; 
    }

     

    function selectFilterInit(field_id, field_name, is_stacked) {

        var from_box = document.getElementById(field_id);
        
        var selector_div_1 = document.getElementsByClassName('related-widget-wrapper')[0];        
        
        var search_by_date_string = getQueryStrings('search_by_date')
        var search_by_date_val  = (search_by_date_string !==undefined && search_by_date_string!='') ? search_by_date_string : '';
 
        //Start Added extra Field MultipleSectOptions 30-08-2018
        var filter_p_2 = document.createElement('div');
        filter_p_2.setAttribute('id','search_by_custom_filter');
        selector_div_1.insertBefore(filter_p_2, selector_div_1.childNodes[0]);
        
        filter_p_2.className_2 = 'selector-filter-by-age';
        var search_filter_label_2 = quickElement('label', filter_p_2, 'Search By Name', 'for', 'search_by_custom_input');
        filter_p_2.appendChild(document.createTextNode(' '));            
        var filter_input_2 = quickElement('input', filter_p_2, '','name','search_by_date','class','vDateField','type', 'text', 'placeholder', gettext("Search By Name"));
        filter_input_2.setAttribute('value',search_by_date_val);
        filter_input_2.id = 'search_by_date';
        var input_submit_btn = quickElement('input', filter_p_2, '', 'class','default','type', 'button','value','Search');
        input_submit_btn.id = 'search_by_submit';
        //End Added extra Field MultipleSectOptions 30-08-2018

    };


    window.addEventListener('load', function(e) {
        $('select.selectfilter, select.selectfilterstacked').each(function() {
            var $el = $(this),
                data = $el.data();
            selectFilterInit($el.attr('id'), data.fieldName, parseInt(data.isStacked, 10));
        });

        $('#search_by_submit').on('click', function(event) {
            var search_by_date = $('#search_by_date').val();
            if(search_by_date!=''){                             
                window.location = '?search_by_date='+search_by_date;
            }            
            else{
                window.location = window.location.href;
            }
        });

    });


    
})(django.jQuery);