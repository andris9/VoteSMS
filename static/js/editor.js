


EDITOR = {
    
    data:[],
    _mode: "normal",
    _cur: 0,
    
    mode: function(mode){
        if(mode==this._mode)
            return false;

        this.update();

        var tdata = [];
        this.data.each((function(data){
            tdata.push(data);
        }).bind(this));
        
        tdata.each((function(data){
            this.remove({}, data);
        }).bind(this));

        this._cur = 0;
        
        this._mode = mode;
        tdata.each((function(data){
            if(data.code.length || data.description.length)
                this.add(data);
        }).bind(this));
        
        if(mode=="edit"){
            this.add();
        }
        return true;
    },
    
    renumber: function(){
        this._cur=0;
        this.data.each((function(data){
            data.row.down("span.nr").innerHTML = ++this._cur;
        }).bind(this));
    },
    
    update: function(){
        if(this._mode!="edit")
            return;
            
        this.data.each((function(data){
            data.code = data.row.down("input.code").value;
            data.description = data.row.down("input.description").value;
        }).bind(this));
    },
    
    create: function(data){
        var row = $("templates").down("#table-"+this._mode+"-row").down("tr").cloneNode(true), elm;
        data = data ||  {
                code:"",
                description:""
            };
        data.row = row;
        this.data.push(data);
        row.down("span.nr").innerHTML = ++this._cur;
        if(this._mode=="edit"){
            row.down("input.code").value = data.code;
            row.down("input.description").value = data.description;
            if(elm = row.down("input.code"))
                elm.observe("keypress",this.keydown.bindAsEventListener(this));
            if(elm = row.down("a.remove"))
                elm.observe("click",this.remove.bindAsEventListener(this, data));
        }else{
            row.down("span.code").innerHTML = data.code;
            row.down("span.description").innerHTML = data.description;
        }
        return data;
    },
    
    keydown: function(event){
        var k = event.charCode || event.keyCode || event.which, 
            chr = String.fromCharCode(k);
            
        if(k>27 && !chr.match(/[\dA-Z]/i))
            Event.stop(event);
    },
    
    remove: function(event, data){
        if(!data || !data.row)
            return;

        this.data.each((function(d, i){
            if(d.row==data.row){
                
                if(data.row && data.row.parentNode){
                    data.row.select("input.code").each((function(input){
                        input.stopObserving();
                    }).bind(this));
                    data.row.select("a").each((function(a){
                        a.stopObserving();
                    }).bind(this));
                    data.row.remove();
                }
                data.row = null;
                this.data.splice(i,1);
                
                throw $break;
            }
        }).bind(this));
        
        
        if(!this.data.length){
            var row = $("templates").down("#table-no-rows").down("tr").cloneNode(true);
            row.id="table-empty-row";
            $("poll_data").insert(row);
        }else{
            this.renumber();
        }
    },
    
    add: function(data){
        data = data || {
            code:"",
            description:""
        }
        data = this.create(data);

        if($("table-empty-row"))
            $("table-empty-row").remove();

        $("poll_data").insert(data.row);
    }
    
}


create_row = function(){
    var row = new Element("tr"),
        remove = new Element("a",{href:"javascript:void(0)"}).update("Remove");
    remove.observe("click",function(){
        remove_row(row);
    });
    
    row.insert(new Element("td").update("1"));
    row.insert(new Element("td").update("2"));
    row.insert(new Element("td").update("3"));
    row.insert(new Element("td").insert(remove));
    return row;
}

remove_row = function(row){
    if(row)
        row.remove();
}

add_row = function(replace){
    var table = $("poll_data"),
        new_row = create_row(),
        tbody=false;
    
    if(replace){
        replace.replace(new_row);
    }else{
        if(tbody = table.down("tbody"))
            tbody.insert(new_row); // TBODY not supported?
        else
            table.insert(new_row);
    }
}