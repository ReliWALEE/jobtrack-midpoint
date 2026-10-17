// Shared by the actual extension and automated extraction tests.
function extractJob(doc=document,href=location.href){
 const candidates=[];
 function visit(value){if(Array.isArray(value)){value.forEach(visit);return;}if(value&&typeof value==='object'){if([].concat(value['@type']||[]).includes('JobPosting'))candidates.push(value);if(value['@graph'])visit(value['@graph']);}}
 for(const script of doc.querySelectorAll('script[type="application/ld+json"]')){try{visit(JSON.parse(script.textContent));}catch{}}
 if(!candidates.length)throw Error('No supported JobPosting data. Use the bundled demo or enter the application manually.');
 const j=candidates[0], loc=[].concat(j.jobLocation||[])[0]?.address||{}, salary=j.baseSalary||{}, value=salary.value||{};
 const salaryValue=value.value; const annual=salary.currency==='USD'&&value.unitText==='YEAR'&&Number.isInteger(salaryValue)&&salaryValue>=0;
 const map={FULL_TIME:'Full-time',PART_TIME:'Part-time',CONTRACTOR:'Contract',INTERN:'Internship'};
 return {company:String(j.hiringOrganization?.name||''),title:String(j.title||''),location:[loc.addressLocality,loc.addressRegion].filter(Boolean).join(', '),salary:annual?salaryValue:null,employment_type:map[[].concat(j.employmentType||[])[0]]||'Full-time',status:'Saved',url:href,notes:'Captured from structured job data. Review all fields before saving.'};
}
if(typeof module!=='undefined')module.exports={extractJob};
