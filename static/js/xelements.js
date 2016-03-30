
String.prototype.format = function() {
    var formatted = this;
    for (var i=0; i<arguments.length; i++) {
        var regexp = new RegExp('\\{'+i+'\\}', 'gi');
        formatted = formatted.replace(regexp, arguments[i]);
    }
    return formatted;
};

var delay = (function() {
    var timer = 0;
    return function(callback, ms) {
        clearTimeout(timer);
        timer = setTimeout(callback, ms);
    };
})();

/*
 * python /opt/web2py/gluon/contrib/websocket_messaging2.py -k web2py4me -p 8080 -l 192.168.200.204
 *
 */
function browserDetect() {
    var ua= navigator.userAgent, tem,
    M= ua.match(/(opera|chrome|safari|firefox|msie|trident(?=\/))\/?\s*(\d+)/i) || [];
    if(/trident/i.test(M[1])){
        tem=  /\brv[ :]+(\d+)/g.exec(ua) || [];
        return 'IE '+(tem[1] || '');
    }
    if(M[1]=== 'Chrome'){
        tem= ua.match(/\b(OPR|Edge)\/(\d+)/);
        if(tem!= null) return tem.slice(1).join(' ').replace('OPR', 'Opera');
    }
    M= M[2]? [M[1], M[2]]: [navigator.appName, navigator.appVersion, '-?'];
    if((tem= ua.match(/version\/(\d+)/i))!= null) M.splice(1, 1, tem[1]);
    return M.join(' ');
}

var tmpt = new Date();
var today = new Date(tmpt.getFullYear(), tmpt.getMonth(), tmpt.getDate());

/* Date function */
function getMonthName(m) {
    var monthNames = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"];
    return monthNames[m];
}
function getShortMonthName(m) {
    var monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"];
    return monthNames[m];
}
function getMonthDigit(m) {
    var months = ['','jan','feb','mar','apr','may','jun','jul','aug','sept','oct','nov','dec'];
    return ('00' + months.indexOf(m.toLowerCase()).toString()).slice(-2);
}

function getDateObj(datestr) {
    if (datestr === '') return '';
    var tmp = datestr.split(/\D/);
    return new Date(tmp[0], --tmp[1], tmp[2]);
}
function getDateStr(date, delim) {
    if (typeof delim === 'undefined') {
        delim = '/';
    }
    var pad = '00';
    var y = date.getFullYear();
    var m = (pad+(date.getMonth()+1)).slice(-pad.length);
    var d = (pad+date.getDate()).slice(-pad.length);
    return m + delim + d + delim + y;
}
function dateparser(d) {
    return getMonthName(d.getMonth()) + ' ' + d.getDate() + ', ' + d.getFullYear();
}
function dateToEpoch(d) {
    // 1 = month, 2=date, 3=year, 4=hour, 5=minute 6=ampm
    var mat = /(\w{3,4})\s(\d{2})\s(\d{4})\s(\d{2}):(\d{2})\s([AP]M)/.exec(d);
    if (mat) {
        var h = +mat[4];
        if (mat[6] === 'AM' && h === 12) {
            h = 0;
        } else if (mat[6] === 'PM' && h !== 12) {
            h += 12;
        }
        var z = new Date(getMonthDigit(mat[1])+'/'+mat[2]+'/'+mat[3]+' '+h+':'+mat[5]+':00');
        return z.getTime();
    } else {
        return d;
    }
}
