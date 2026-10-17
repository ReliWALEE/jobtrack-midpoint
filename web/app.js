const $=s=>document.querySelector(s), statuses=['Saved','Applied','Interview','Offer','Rejected'], types=['Full-time','Part-time','Contract','Internship'];
for(const [select,values] of [['#status',statuses],['#type',types],['[name=status]',statuses],['[name=employment_type]',types]]) for(const v of values) $(select).add(new Option(v,v));
let records=[],editing=null,request=0;
async function api(path,options){const response=await fetch('/api/'+path,options);const data=await response.json();if(!response.ok)throw Error(data.error||'Request failed');return data;}
function text(tag,value){const e=document.createElement(tag);e.textContent=value;return e;}
async function load(){const version=++request;try{
const q=new URLSearchParams();for(const [id,key] of [['search','q'],['status','status'],['type','employment_type'],['min','salary_min'],['max','salary_max']])if($('#'+id).value)q.set(key,$('#'+id).value);
const [sort,direction]=$('#sort').value.split(':');q.set('sort',sort);q.set('direction',direction);
const [rows,all]=await Promise.all([api('applications?'+q),api('applications')]);if(version!==request)return;records=all;
$('#total').textContent=all.length;$('#progress').textContent=all.filter(x=>['Saved','Applied','Interview'].includes(x.status)).length;$('#interviews').textContent=all.filter(x=>x.status==='Interview').length;$('#offers').textContent=all.filter(x=>x.status==='Offer').length;
$('#count').textContent=rows.length+' opportunities shown';$('#rows').replaceChildren();$('#empty').hidden=rows.length>0;
for(const row of rows){const tr=document.createElement('tr');let td=document.createElement('td');td.append(text('strong',row.title),text('small',row.company));tr.append(td);
td=document.createElement('td');td.append(text('span',row.location||'—'),text('small',row.employment_type));tr.append(td);tr.append(text('td',row.salary===null?'Not listed':new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(row.salary)));
td=document.createElement('td');const badge=text('span',row.status);badge.className='badge '+row.status;td.append(badge);tr.append(td,text('td',row.applied_date));td=document.createElement('td');td.className='actions';
for(const [label,action] of [['Edit',()=>open(row)],['Delete',async()=>{if(confirm('Delete '+row.title+' at '+row.company+'?'))try{await api('applications/'+row.id,{method:'DELETE'});await load();}catch(e){$('#message').textContent=e.message;}}]]){const button=text('button',label);button.setAttribute('aria-label',label+' '+row.title);button.onclick=action;td.append(button);}tr.append(td);$('#rows').append(tr);}$('#message').textContent='';
}catch(e){if(version===request)$('#message').textContent='Could not load applications: '+e.message;}}
function open(row={}){editing=row.id||null;$('#application').reset();$('#form-error').textContent='';$('#form-title').textContent=editing?'Edit application':'Add application';const defaults={status:'Saved',employment_type:'Full-time',applied_date:new Date().toLocaleDateString('en-CA')};for(const el of $('#application').elements)if(el.name)el.value=row[el.name]??defaults[el.name]??'';$('#editor').showModal();}
$('#add').onclick=()=>open();$('#close').onclick=()=>$('#editor').close();$('#filters').onsubmit=e=>e.preventDefault();$('#filters').oninput=load;$('#reset').onclick=()=>{HTMLFormElement.prototype.reset.call($('#filters'));load();};
$('#application').onsubmit=async e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.target));data.salary=data.salary===''?null:Number(data.salary);$('#save').disabled=true;try{await api('applications'+(editing?'/'+editing:''),{method:editing?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});$('#editor').close();await load();}catch(e){$('#form-error').textContent=e.message;}finally{$('#save').disabled=false;}};
load();
if(location.hash.startsWith('#import=')){try{const draft=JSON.parse(decodeURIComponent(location.hash.slice(8)));history.replaceState(null,'',location.pathname);open(draft);}catch{$('#message').textContent='Could not read imported draft. Please add the application manually.';}}
