//////////////////////////////////
// Centillion Master List
// Javascript Functions 
//
// This file contains javascript functions used by
// the master_list page of centillion. The master
// list page uses the search engine as an API to
// get a list of all documents by type.


///////////////////////////////////
// Process get parameters
//
// When the document is loaded, parse the GET params
// from the URL (everything after the ?).
//
// If the "doctype" parameter is in the URL, use it to
// determine which panel to open automatically.

var initGdocTable = false;
var initIssuesTable = false;
var initGhfilesTable = false;
var initMarkdownTable = false;
var initDisqusTable = false;

$(document).ready(function() {
    var url_string = document.location.toString();
    var url = new URL(url_string);
    var d = url.searchParams.get("doctype");

    if (d==='gdoc') {
        load_gdoc_table();
        var divList = $('div#collapseDrive').addClass('in');

    } else if (d==='issue') {
        load_issue_table();
        var divList = $('div#collapseIssues').addClass('in');

    } else if (d==='ghfile') {
        load_ghfile_table();
        var divList = $('div#collapseFiles').addClass('in');

    } else if (d==='markdown') {
        load_markdown_table();
        var divList = $('div#collapseMarkdown').addClass('in');

    } else if (d==='disqus') {
        load_disqusthreads_table();
        var divList = $('div#collapseDisqus').addClass('in');

    }
});


//////////////////////////////////
// utility functions

// https://stackoverflow.com/a/25275808
function iso8601(date) {
  var hours = date.getHours();
  var minutes = date.getMinutes();
  var ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12;
  hours = hours ? hours : 12; // the hour '0' should be '12'
  minutes = minutes < 10 ? '0'+minutes : minutes;
  var strTime = hours + ':' + minutes + ' ' + ampm;
  return date.getYear() + "-" + (date.getMonth()+1) + "-" + date.getDate() + "  " + strTime;
}

// https://stackoverflow.com/a/7390612
var toType = function(obj) {
  return ({}).toString.call(obj).match(/\s([a-zA-Z]+)/)[1].toLowerCase()
}

//////////////////////////////////
// API-to-Table Functions
//
// These functions ask centillion for a list of all documents
// of a given type, and load the results into an HTML table.
//
// The dataTable bootstrap plugin is used to make the tables
// sortable, searchable, and slick.
//
// Sections:
// ----------
// Google Drive files
// Github issues
// Github files
// Github markdown

// ------------------------
// Google Drive

function load_gdoc_table(){
    if(!initGdocTable) {
        var divList = $('div#collapseDrive').attr('class');
        if (divList.indexOf('in') !== -1) {
            //console.log('Closing Google Drive master list');
        } else { 
            //console.log('Opening Google Drive master list');

            $.getJSON("/list/gdoc", function(result){

                var r = new Array(), j = -1, size=result.length;
                r[++j] = '<thead>'
                r[++j] = '<tr class="header-row">';
                r[++j] = '<th width="40%">File Name</th>';
                r[++j] = '<th width="15%">Owner</th>';
                r[++j] = '<th width="15%">Type</th>';
                r[++j] = '<th width="15%">Created</th>';
                r[++j] = '<th width="15%">Modified</th>';
                r[++j] = '</tr>';
                r[++j] = '</thead>'
                r[++j] = '<tbody>'
                for (var i=0; i<size; i++){
                    r[++j] = '<tr><td>';
                    r[++j] = '<a href="' + result[i]['url'] + '" target="_blank">'
                    r[++j] = result[i]['title'];
                    r[++j] = '</a>'
                    r[++j] = '</td><td>';
                    r[++j] = result[i]['owner_name'];
                    r[++j] = '</td><td>';
                    r[++j] = result[i]['mimetype'];
                    r[++j] = '</td><td>';
                    r[++j] = result[i]['created_time'];
                    r[++j] = '</td><td>';
                    r[++j] = result[i]['modified_time'];
                    r[++j] = '</td></tr>';
                }
                r[++j] = '</tbody>'

                // Construct names of id tags
                var doctype = 'gdocs';
                var idlabel = '#' + doctype + '-master-list';
                var filtlabel = idlabel + '_filter';

                // Initialize the DataTable
                $(idlabel).html(r.join(''));
                $(idlabel).DataTable({
                    responsive: true,
                    lengthMenu: [50,100,250,500]
                });

                initGdocTable = true
            });
            //console.log('Finished loading Google Drive master list');
        }
    }
}

// ------------------------
// Github issues

function load_issue_table(){
    if(!initIssuesTable) {
        var divList = $('div#collapseIssues').attr('class');
        if (divList.indexOf('in') !== -1) {
            //console.log('Closing Github issues master list');
        } else { 
            //console.log('Opening Github issues master list');

            $.getJSON("/list/issue", function(result){
                var r = new Array(), j = -1, size=result.length;
                r[++j] = '<thead>'
                r[++j] = '<tr class="header-row">';
                r[++j] = '<th width="50%">Issue/PR Name</th>';
                r[++j] = '<th width="15%">Repository</th>';
                r[++j] = '<th width="15%">Created</th>';
                r[++j] = '<th width="15%">Modified</th>';
                r[++j] = '</tr>';
                r[++j] = '</thead>'
                r[++j] = '<tbody>'
                for (var i=0; i<size; i++){
                    r[++j] ='<tr><td>';
                    r[++j] = '<a href="' + result[i]['url'] + '" target="_blank">'
                    r[++j] = result[i]['title'];
                    r[++j] = '</a>'
                    r[++j] = '</td><td>';
                    r[++j] = '<a href="' + result[i]['repo_url'] + '" target="_blank">'
                    r[++j] = result[i]['repo_name'];
                    r[++j] = '</a>'
                    r[++j] = '</td><td>';
                    r[++j] = result[i]['created_time'];
                    r[++j] = '</td><td>';
                    r[++j] = result[i]['modified_time'];
                    r[++j] = '</td></tr>';
                }
                r[++j] = '</tbody>'

                // Construct names of id tags
                var doctype = 'issues';
                var idlabel = '#' + doctype + '-master-list';
                var filtlabel = idlabel + '_filter';

                // Initialize the DataTable
                $(idlabel).html(r.join(''));
                $(idlabel).DataTable({
                    responsive: true,
                    lengthMenu: [50,100,250,500]
                });

                initIssuesTable = true;
            });
            //console.log('Finished loading Github issues master list');
        }
    }
}

// ------------------------
// Github files

function load_ghfile_table(){
    if(!initGhfilesTable) {
        var divList = $('div#collapseFiles').attr('class');
        if (divList.indexOf('in') !== -1) {
            //console.log('Closing Github files master list');
        } else { 
            //console.log('Opening Github files master list');

            $.getJSON("/list/ghfile", function(result){
                //console.log("-----------");
                //console.log(result);
                var r = new Array(), j = -1, size=result.length;
                r[++j] = '<thead>'
                r[++j] = '<tr class="header-row">';
                r[++j] = '<th width="70%">File Name</th>';
                r[++j] = '<th width="30%">Repository</th>';
                r[++j] = '</tr>';
                r[++j] = '</thead>'
                r[++j] = '<tbody>'
                for (var i=0; i<size; i++){
                    r[++j] ='<tr><td>';
                    r[++j] = '<a href="' + result[i]['url'] + '" target="_blank">'
                    r[++j] = result[i]['title'];
                    r[++j] = '</a>'
                    r[++j] = '</td><td>';
                    r[++j] = '<a href="' + result[i]['repo_url'] + '" target="_blank">'
                    r[++j] = result[i]['repo_name'];
                    r[++j] = '</a>'
                    r[++j] = '</td></tr>';
                }
                r[++j] = '</tbody>'

                // Construct names of id tags
                var doctype = 'ghfiles';
                var idlabel = '#' + doctype + '-master-list';
                var filtlabel = idlabel + '_filter';

                // Initialize the DataTable
                $(idlabel).html(r.join(''));
                $(idlabel).DataTable({
                    responsive: true,
                    lengthMenu: [50,100,250,500]
                });

                initGhfilesTable = true;
            });
            //console.log('Finished loading Github file list');
        }
    }
}

// ------------------------
// Github Markdown

function load_markdown_table(){
    if(!initMarkdownTable) { 
        var divList = $('div#collapseMarkdown').attr('class');
        if (divList.indexOf('in') !== -1) {
            //console.log('Closing Github markdown master list');
        } else { 
            //console.log('Opening Github markdown master list');

            $.getJSON("/list/markdown", function(result){
                var r = new Array(), j = -1, size=result.length;
                r[++j] = '<thead>'
                r[++j] = '<tr class="header-row">';
                r[++j] = '<th width="70%">Markdown File Name</th>';
                r[++j] = '<th width="30%">Repository</th>';
                r[++j] = '</tr>';
                r[++j] = '</thead>'
                r[++j] = '<tbody>'
                for (var i=0; i<size; i++){
                    r[++j] ='<tr><td>';
                    r[++j] = '<a href="' + result[i]['url'] + '" target="_blank">'
                    r[++j] = result[i]['title'];
                    r[++j] = '</a>'
                    r[++j] = '</td><td>';
                    r[++j] = '<a href="' + result[i]['repo_url'] + '" target="_blank">'
                    r[++j] = result[i]['repo_name'];
                    r[++j] = '</a>'
                    r[++j] = '</td></tr>';
                }
                r[++j] = '</tbody>'

                // Construct names of id tags
                var doctype = 'markdown';
                var idlabel = '#' + doctype + '-master-list';
                var filtlabel = idlabel + '_filter';

                // Initialize the DataTable
                $(idlabel).html(r.join(''));
                $(idlabel).DataTable({
                    responsive: true,
                    lengthMenu: [50,100,250,500]
                });

                initMarkdownTable = true;
            });
            //console.log('Finished loading Markdown list');
        }
    }
}


// ------------------------
// Disqus Comment Threads

function load_disqusthreads_table(){
    if(!initDisqusTable) { 
        var divList = $('div#collapseDisqus').attr('class');
        if (divList.indexOf('in') !== -1) {
            console.log('Closing Disqus comment threads master list');
        } else { 
            console.log('Opening Disqus comment threads master list');
    
            $.getJSON("/list/disqus", function(result){
                var r = new Array(), j = -1, size=result.length;
                r[++j] = '<thead>'
                r[++j] = '<tr class="header-row">';
                r[++j] = '<th width="70%">Page Title</th>';
                r[++j] = '<th width="30%">Created</th>';
                r[++j] = '</tr>';
                r[++j] = '</thead>'
                r[++j] = '<tbody>'
                for (var i=0; i<size; i++){
                    r[++j] ='<tr><td>';
                    r[++j] = '<a href="' + result[i]['url'] + '" target="_blank">'
                    r[++j] = result[i]['title'];
                    r[++j] = '</a>'
                    r[++j] = '</td><td>';
                    r[++j] = result[i]['created_time'];
                    r[++j] = '</td></tr>';
                }
                r[++j] = '</tbody>'

                // Construct names of id tags
                var doctype = 'disqus';
                var idlabel = '#' + doctype + '-master-list';
                var filtlabel = idlabel + '_filter';

                // Initialize the DataTable
                $(idlabel).html(r.join(''));
                $(idlabel).DataTable({
                    responsive: true,
                    lengthMenu: [50,100,250,500]
                });

                initDisqusTable = true;
            });
            console.log('Finished loading Disqus comment threads list');
        }
    }
}

