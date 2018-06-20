/*---------------------------------------------------------
 * OpenERP web_list_columns
 *---------------------------------------------------------*/
openerp.ow_dynamic_list = function (instance) {
    var _t = instance.web._t,
       _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    var ListView = instance.web.ListView;

    ListView.include({
        init: function(parent, dataset, view_id, options) {
            var self = this;
	        var uid = parent.session.uid;
			var th_model = new instance.web.Model("dynamic.fields");
			self.precheck_li();
			self.th_columns = []
            dataset.call("fields_get",[[]]).then(function(results){
                self.fields_get = results;
            });
	        th_model.call("search_read", [[['view_id', '=', view_id],
									['user_id', '=', uid]], ['dynamic_list_text']]).then(function(result){
	        	if(result.length > 0){
	        		self.col_list = _.filter(JSON.parse(result[0].dynamic_list_text), function(elem){return elem.visible});
					self.th_columns = _.pluck(self.col_list, 'name');
	        	}
	        });

            this._super(parent, dataset, view_id, options);
        },
        fetch_invisible_fields: function(data){
        	this.invisible_fields = {};
        	this.invisible_field_names = [];
        	for(var i in data.arch.children){
        		if(data.arch.children[i].attrs.modifiers){
        			var modifiers = JSON.parse(data.arch.children[i].attrs.modifiers);
            		if(modifiers.tree_invisible && data.arch.children[i].tag == 'field'){
            			this.invisible_fields[data.arch.children[i].attrs.name] = data.arch.children[i];
            			this.invisible_field_names.push(data.arch.children[i].attrs.name);
            		}
        		}
            }
        },
        precheck_li: function(){
            var self = this;
        	var dataseq = 0;
        	self.default_list = [];
            for(var i in self.visible_columns){
                self.$DColumns.find("#" + self.visible_columns[i].name).prop('checked',true).attr('data-seq', dataseq);
                this.col_list.push({'name': self.visible_columns[i].name, 'visible': true, 'seq': dataseq});
                self.default_list.push(self.visible_columns[i].name);
                dataseq = dataseq + 1;
            }
        	return dataseq;
        },

        load_list: function(data) {
            var self = this;
            var uid = this.session.uid;
            self.th_fields_view = data;
            var col_values = self.prepare_col_vals();
            self.fetch_invisible_fields(data);

            if (self.th_columns.length> 0){
                self.render_fields();
                this._super(self.th_fields_view);
            }
            else{
                this._super(data);
            }

            if(!self.$DColumns){
                self.$DColumns = $(QWeb.render("ListView.columns",{'fields': col_values}));
                self.$pager.append(self.$DColumns);
                self.render_dynamic_list_events();
            }
            self.sort_elements();

        },

        sort_elements: function(){
        	var self = this;
//			var elems = $(self.$DColumns[2]).find('#dycollist');
            var elems = $('#dynamicList #dycollist');
			elems.sort(function(a, b) {
			    if (parseInt($(a).find('input').attr('data-seq')) < parseInt($(b).find('input').attr('data-seq')))
			    return -1;
			    if (parseInt($(a).find('input').attr('data-seq')) > parseInt($(b).find('input').attr('data-seq')))
			    return 1; return 0;
			}).appendTo(elems.parent());

			self.$DColumns.find('.th_ul li:last-child').after(self.$DColReset);
		},

		prepare_col_vals: function(){
        	var self = this;
        	var col_vals = [];
        	_.each(this.fields_get, function(field, fieldName) {
	        	if (field.type != 'many2many'  && field.type != 'one2many'){
	        		col_vals.push({string: field.string, name: fieldName, data_string: field.string.toLowerCase()});
	        	}
	        });
        	return col_vals;
        },

        render_dynamic_list_events: function(){
            var self = this;
            this.col_list = [];
            var seq = self.precheck_li() - 1;

            self.$DColumns.find('#dycollist').each(function(){
                $(this).attr('data-search-term', $(this).find('span').text().toLowerCase());
            });

            self.$DColumns.find("#dycolsrch").on('keyup', function(){
                var searchTerm = $(this).val().toLowerCase();
                $('.th_ul #dycollist').each(function(){
                    if ($(this).filter('[data-search-term *= ' + searchTerm + ']').length > 0 || searchTerm.length < 1) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });
            });

            self.$DColumns.find('#dynamicList').click(function (e) {
				e.stopPropagation();
            });

            self.$DColReset = $(QWeb.render("th_list_reset",{}));

            self.$DColumns.find('.th_ul').sortable({
                 cancel: ".no-sort",
                 placeholder: "ui-state-highlight",
                 axis: "y",
                 items: "li:not(.no-sort)",
                 update : function( event, ul) {
                     $('.th_ul #dycollist').each(function(i){
                        $(this).find('input').attr('data-seq', i);
                        //updates the self.col_list sequence
                        var input_name = $(this).find('input').attr('name');
                        var col_field = _.find(self.col_list, function(item){
                            return item.name == input_name;
                        });
                        if (col_field !== undefined ){col_field.seq = i};
                     });
                     self.col_list = _.sortBy(self.col_list, function(o) { return o.seq;});
                     var col_names = [];
                     $('#dycollist input:checked').each(function() {
                         col_names.push($(this).attr('name'));
                     });
                     //push only checked data
                     self.th_columns = col_names;
                     self.render_fields();
                     self.alive(self.load_view(self.session.user_context)).then(self.proxy('reload_content'));
                 },
            });

            self.$DColumns.find('.columnCheckbox').change(function (e){
                var val_checked = $("#"+this.id).prop("checked");
                if (val_checked){
                    seq = seq + 1;
                    var id_search = _.findWhere(self.col_list,{name:this.id});
                    if (typeof id_search == "undefined"){
                        self.col_list.push({'name':this.id,'visible':true,'seq':seq});
                    }else{id_search.visible = true;id_search.seq = seq;}
                }
                else{
                    var id_search = _.findWhere(self.col_list,{name:this.id});
                    if (typeof id_search == "undefined"){
                        self.col_list.push({'name':this.id,'visible':false,'seq':100});
                    }else{id_search.visible = false;id_search.seq = 100;}
                }

                self.col_list = _.sortBy(self.col_list, function(o) { return o.seq;});

                var col_names = _.pluck(self.col_list, 'name');
                self.th_columns = col_names;
                self.sort_elements();
                self.render_fields();
                self.alive(self.load_view(self.session.user_context)).then(self.proxy('reload_content'));
            });

            self.$DColReset.find('#restore_list').click(function(e){
                var uid = self.session.uid;
                var th_model = new instance.web.Model("dynamic.fields");
                th_model.call('search', [[["view_id", "=", self.fields_view.view_id],["user_id", "=", uid]]]).then(function(results){
                    if (!_.isEmpty(results)){
                        th_model.call('unlink', results, {}).done(function(){
                            location.reload();
                        });
                    }
                });
            });
        },

        render_fields: function(){
			var self = this;
			self.th_fields_view.arch.children = [];
			self.th_fields_view.fields = {};
        	for(var i in self.th_columns){
        		var cname = self.th_columns[i];
        		var search_col = _.findWhere(self.col_list,{name: cname});
        		if(search_col && search_col.visible && search_col.visible == true){
        			self.th_fields_view.fields[cname] = self.fields_get[cname];
        			self.th_fields_view.arch.children.push({
        				attrs:{
    	                    modifiers: '{}',
    	                    name: cname,
    	                },
    	                children: [],
    	                tag: 'field'
        			});
        		}
        		else if($.inArray(cname, self.default_list))
        		{
        			self.th_fields_view.fields[cname] = self.fields_get[cname];
        			self.th_fields_view.arch.children.push({
        				attrs:{
    	                    modifiers: '{"tree_invisible": true}',
    	                    name: cname,
    	                },
    	                children: [],
    	                tag: 'field'
        			});
        		}
        	}
        	for(var i in self.invisible_field_names){
        		self.th_fields_view.arch.children.push(self.invisible_fields[self.invisible_field_names[i]]);
        		self.col_list.push({'name':this.id,'visible':false,'seq':100});
        	}
        	self.th_fields_view.arch.children = _.uniq(self.th_fields_view.arch.children, function(item){
            	return item.attrs.name;
            });
        	self.store_current_state();
        	self.col_list = _.reject(self.col_list, function(item){
        		return item.name === null;
        	});
		},

        store_current_state: function(){
			var self = this;
			var uid = this.session.uid;
			var th_model = new instance.web.Model("dynamic.fields");

            self.col_list = _.filter(self.col_list,function (value) {
                return value.name !==null;

            })
            self.col_list = _.filter(self.col_list,function (value) {
                return typeof value.name != 'undefined';
            })


			th_model.call('search', [[["view_id", "=", self.fields_view.view_id],["user_id", "=", uid]]]).then(function(results){
				if(results.length==1){
					th_model.call('write', [results, {
        				'dynamic_list_text': JSON.stringify(self.col_list),
        			}]);
        		}else{
        			th_model.call('create', [{
        				'view_id': self.fields_view.view_id,
        				'dynamic_list_text': JSON.stringify(self.col_list),
        				'user_id': uid,
        			}]);
        		}
			})
		},
    });
};

