$(document).ready(function() {

var aj = null;

$('.req-wrap span').on('click', function() {
    $('#req_form').submit();
});


$('#req_form').submit(function(e) {

    if (aj) aj.abort();

    e.preventDefault();
    var r = $('#req').val();
    if (r.length == 0) {
        alert('Please type your request.');
        return;
    } else {
        var html = '',
        bl = {
            s:   '<div class="res-item">',
            h2s: '<h2 class="title">',
            h2e: '</h2>',
            l:   '<div class="link">',
            t:   '<div class="summary">',
            as:  '<a target="_blank" href="',
            ah:  '">',
            ae:  '</a>',
            e:   '</div>',
            no:  'No result.',
            img: '<img src="/static/image/ajax-loader.gif" />'
        };


        aj = $.ajax({
            url: "/q",
            type: "post",
            data: {
                query: r
            },
            cache: false,
            beforeSend: function() {
                 $('.result').html(bl.img);
            },
            success: function(msg) {
                
                aj = null;
                res = msg.items;

                if (res.length > 0) {
                    for (var key in res) {
                        html += bl.s;
                            html += bl.h2s + res[key].title + bl.h2e;
                            html += bl.l + bl.as + res[key].link + bl.ah + res[key].link + bl.ae + bl.e;
                            html += bl.t + res[key].summary + bl.e;
                        html += bl.e;
                    }
                } else {
                    html += bl.no;
                }

                $('.result').fadeOut(150, function() {
                    $(this).html(html).fadeIn(150);
                });
            }
        });

    }

});

});