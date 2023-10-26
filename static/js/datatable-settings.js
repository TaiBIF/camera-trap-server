// datatable language settings
let language_settings = {
	"decimal": "",
	"emptyTable": "查無資料",
	"info": "正在檢視第 _START_ 至 _END_ 筆，總共 _TOTAL_ 筆",
	"infoEmpty": "共 0 筆",
	"infoFiltered": "",
	"infoPostFix": "",
	"thousands": ",",
	"lengthMenu": `每頁顯示 _MENU_ 筆`,
	"loadingRecords": "載入中...",
	"processing": "",
	"zeroRecords": "查無符合資料",
	"paginate": {
		// "next": '下一頁<svg xmlns="http://www.w3.org/2000/svg" width="9.187" height="17.053" viewBox="0 0 9.187 17.053"><g id="next" transform="translate(-102.297 0)"><g id="Group_17" data-name="Group 17" transform="translate(102.297 0)"><path id="Path_59" data-name="Path 59" d="M111.291,8.059,103.417.185a.656.656,0,0,0-.928.928L109.9,8.523l-7.411,7.411a.656.656,0,0,0,.928.928l7.874-7.874A.656.656,0,0,0,111.291,8.059Z" transform="translate(-102.297 0)" fill="#529a81"/></g></g></svg>',
		"next": '下一頁',
		// "previous": '<svg xmlns="http://www.w3.org/2000/svg" width="9.187" height="17.053" viewBox="0 0 9.187 17.053"><g id="pre" transform="translate(111.483 17.054) rotate(180)"><g id="Group_17" data-name="Group 17" transform="translate(102.297 0)"><path id="Path_59" data-name="Path 59" d="M111.291,8.059,103.417.185a.656.656,0,0,0-.928.928L109.9,8.523l-7.411,7.411a.656.656,0,0,0,.928.928l7.874-7.874A.656.656,0,0,0,111.291,8.059Z" transform="translate(-102.297 0)" fill="#529a81"/></g></g></svg> 上一頁'
		"previous": '上一頁'
	}
};

//  datatable automatically fits window height
(function (factory) {
	if (typeof define === 'function' && define.amd) {
		// AMD
		define(['jquery', 'datatables.net'], function ($) {
			return factory($, window, document);
		});
	}
	else if (typeof exports === 'object') {
		// CommonJS
		module.exports = function (root, $) {
			if (!root) {
				root = window;
			}

			if (!$ || !$.fn.dataTable) {
				$ = require('datatables.net')(root, $).$;
			}

			return factory($, root, root.document);
		};
	}
	else {
		// Browser
		factory(jQuery, window, document);
	}
}(function ($, window, document, undefined) {
	'use strict';
	var ScrollResize = function (dt) {
		var that = this;
		var table = dt.table();

		this.s = {
			dt: dt,
			host: $(table.container()).parent(),
			header: $(table.header()),
			footer: $(table.footer()),
			body: $(table.body()),
			container: $(table.container()),
			table: $(table.node())
		};

		var host = this.s.host;
		if (host.css('position') === 'static') {
			host.css('position', 'relative');
		}

		dt.on('draw', function () {
			that._size();
		});

		this._attach();
		this._size();
	};


	ScrollResize.prototype = {
		_size: function () {
			var settings = this.s;
			var dt = settings.dt;
			var t = dt.table();
			var offsetTop = $(settings.table).offset().top;
			var availableHeight = settings.host.height();
			var scrollBody = $('div.dataTables_scrollBody', t.container());

			// Subtract the height of the header, footer and the elements
			// surrounding the table
			// availableHeight -= offsetTop;
			// availableHeight -= settings.container.height() - (offsetTop + scrollBody.height());

			$('div.dataTables_scrollBody', t.container()).css({
				maxHeight: '1266px',
				height: '100%',
				maxWidth: '100%',
				width: '100%'
			});

			$('div.dataTables_scrollHead', t.container()).css({
				maxWidth: '100%',
				width: '100%'
			});


			if (dt.fixedColumns) {
				dt.fixedColumns().relayout();
			}
		},

		_attach: function () {
			// There is no `resize` event for elements, so to trigger this effect,
			// create an empty HTML document using an <iframe> which will issue a
			// resize event inside itself when the document resizes. Since it is
			// 100% x 100% that will occur whenever the host element is resized.
			var that = this;
			var obj = $('<iframe/>')
				.css({
					position: 'absolute',
					top: 0,
					left: 0,
					height: '100%',
					width: '100%',
					zIndex: -1,
					border: 0
				})
				.attr('frameBorder', '0')
				.attr('src', 'about:blank');

			obj[0].onload = function () {
				var body = this.contentDocument.body;
				var height = body.offsetHeight;
				var contentDoc = this.contentDocument;
				var defaultView = contentDoc.defaultView || contentDoc.parentWindow;

				defaultView.onresize = function () {
					// Three methods to get the iframe height, to keep all browsers happy
					var newHeight = body.clientHeight || body.offsetHeight;
					var docClientHeight = contentDoc.documentElement.clientHeight;

					if (!newHeight && docClientHeight) {
						newHeight = docClientHeight;
					}

					if (newHeight !== height) {
						height = newHeight;

						that._size();
					}
				};
			};

			obj
				.appendTo(this.s.host)
				.attr('data', 'about:blank');
		}
	};

	$.fn.dataTable.ScrollResize = ScrollResize;
	$.fn.DataTable.ScrollResize = ScrollResize;

	// Automatic initialisation listener
	$(document).on('init.dt', function (e, settings) {
		if (e.namespace !== 'dt') {
			return;
		}

		var api = new $.fn.dataTable.Api(settings);

		if (settings.oInit.scrollResize || $.fn.dataTable.defaults.scrollResize) {
			new ScrollResize(api);
		}
	});

}));
