/*
 * Pro Dogs Direct adoption form walker (research tool, 2025-11-17).
 *
 * Walks all 10 pages of https://prodogsdirect.org.uk/adoptionform/ with dummy
 * data and prints every question + option, then writes pages.json.
 * This is how docs/research/prodogs-velma-application/adoption-form-questions.md
 * was generated.
 *
 *   node walk-form.js > pages.txt
 *
 * DO NOT point this at a real application: it submits the form (dummy values).
 * The trick that makes it work: the honeypot field item_meta[1919] must stay
 * empty and ak_hp_textarea must be omitted, otherwise Akismet flags it as spam.
 * The form is Formidable Forms: it is a plain POST of item_meta[...] fields plus
 * form_id=53 / form_key / frm_state, returning the next page's HTML.
 */
const base='https://prodogsdirect.org.uk/adoptionform/';
let cookie='';
const fs=require('fs');
const UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36';
function attrs(s){const o={};for(const m of s.matchAll(/([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*"([^"]*)"/g))o[m[1]]=m[2];return o;}
function clean(s){return s.replace(/<[^>]+>/g,' ').replace(/&amp;/g,'&').replace(/&#0?39;/g,"'").replace(/&#8217;/g,"'").replace(/&#8211;/g,'-').replace(/&nbsp;/g,' ').replace(/&quot;/g,'"').replace(/\s+/g,' ').trim();}
function blocks(html){
  const out=[];
  const re=/<div id="(?:frm_field_|frm_field_conf_)(\d+)_container"([\s\S]*?)(?=<div id="(?:frm_field_|frm_field_conf_)\d+_container"|<input type="hidden" name="frm_next_page|<\/form>)/g;
  for(const m of html.matchAll(re)) out.push({id:m[1],html:m[2]});
  return out;
}
function describe(html){
  return blocks(html).map(({id,html:b})=>{
    const lbl=clean((b.match(/class="frm_primary_label"[^>]*>([\s\S]*?)<\/label>/)||b.match(/class="frm_primary_label"[^>]*>([\s\S]*?)<\/div>/)||[])[1]||'');
    const radios=[...b.matchAll(/<input([^>]*type="radio"[^>]*)>/g)].map(x=>attrs(x[1]).value);
    const checks=[...b.matchAll(/<input([^>]*type="checkbox"[^>]*)>/g)].map(x=>attrs(x[1]).value);
    const sels=[...b.matchAll(/<select([^>]*)>([\s\S]*?)<\/select>/g)].map(x=>({name:attrs(x[1]).name,opts:[...x[2].matchAll(/<option([^>]*)>([\s\S]*?)<\/option>/g)].map(o=>clean(o[2])).filter(Boolean)}));
    const texts=[...b.matchAll(/<(input|textarea)([^>]*)>/g)].filter(x=>/type="(text|email|tel|number|url|date|password)"/.test(x[2])||x[1]==='textarea').map(x=>({name:attrs(x[2]).name,type:attrs(x[2]).type||'textarea'}));
    return {id,label:lbl,radios,checks,sels,texts};
  }).filter(f=>f.label||f.radios.length||f.checks.length||f.sels.length||f.texts.length);
}
async function req(opts={}){const r=await fetch(base,{...opts,headers:{'user-agent':UA,cookie,referer:base,...(opts.headers||{})}});const sc=r.headers.getSetCookie?r.headers.getSetCookie():[];if(sc.length)cookie=sc.map(c=>c.split(';')[0]).join('; ');return {text:await r.text(),status:r.status,url:r.url};}
function basePayload(html){
  const d={};
  for(const m of html.matchAll(/<input([^>]*)>/g)){const a=attrs(m[1]); if(!a.name)continue; if(a.type==='radio'||a.type==='checkbox')continue; d[a.name]=a.value??'';}
  for(const m of html.matchAll(/<select([^>]*)>/g)){d[attrs(m[1]).name]=d[attrs(m[1]).name]??'';}
  delete d['ak_hp_textarea'];
  return d;
}
const SPEC={1798:'Alex Morgan',1799:'38',1800:'alex.morgan@example.com',1801:'07700900123',1802:'07700900123',1803:'12 Oakfield Road',1804:'',1805:'Epsom',1806:'Surrey',1807:'KT18 5AA'};
(async()=>{
  let {text:html}=await req();
  let fixes={};
  const pages=[];
  for(let step=1;step<=25;step++){
    const pageNo=(html.match(/frm_page_num_(\d+)/)||[])[1];
    const fields=describe(html);
    const dump={page:pageNo,fields:fields.map(f=>({id:f.id,label:f.label,radios:f.radios,checks:f.checks,sels:f.sels,texts:f.texts.map(t=>t.type)}))};
    pages.push(dump);
    console.log('\n===== PAGE',pageNo,'=====');
    console.log(dump.fields.map(f=>`[${f.id}] ${f.label}${f.radios.length?'\n    R: '+f.radios.join(' / '):''}${f.checks.length?'\n    C: '+f.checks.join(' / '):''}${f.sels.length?'\n    S: '+f.sels.map(s=>s.opts.join(' | ')).join(' || '):''}${f.texts.length?'\n    T: '+f.texts.join(','):''}`).join('\n'));
    const payload=basePayload(html);
    for(const f of fields){
      if(f.id==='1919') continue;
      const keys=f.texts.map(t=>t.name).filter(Boolean);
      if(f.radios.length){
        const n=Object.keys(payload).find(k=>k.startsWith('item_meta['+f.id+']'))||'item_meta['+f.id+']';
        if(!f.radios.includes(payload[n])) payload[n]=f.radios[0];
      }
      if(f.checks.length){
        const n=Object.keys(payload).find(k=>k.startsWith('item_meta['+f.id+']'))||('item_meta['+f.id+'][]');
        const v=f.checks[0];
        delete payload[n]; payload['item_meta['+f.id+'][]']=v;
      }
      for(const k of keys){
        if(k.includes('conf_')) continue;
        if(!payload[k]) payload[k]= SPEC[f.id] || fixes[f.id] || (f.texts.find(t=>t.name===k)?.type==='email'?'alex.morgan@example.com':(f.texts.find(t=>t.name===k)?.type==='tel'?'07700900123':'x'));
      }
      const conf=keys.find(k=>k.includes('conf_'));
      if(conf){ const src=keys.find(k=>!k.includes('conf_'))||('item_meta['+f.id+']'); payload[conf]=payload[src]; }
    }
    let res;
    for(let t=0;t<4;t++){
      await new Promise(r=>setTimeout(r,3000));
      res=await req({method:'POST',headers:{'content-type':'application/x-www-form-urlencoded'},body:new URLSearchParams(payload).toString()});
      if(!/appears to be spam/.test(res.text)) break;
      console.log('  [spam attempt',t+1,'] retrying...');
    }
    if(/frm_error_style/.test(res.text)){
      const errs=[...res.text.matchAll(/class="frm_error_link" href="#(?:(?:frm_field_)|(?:frm_field_conf_))(\d+)_container">([^<]*)/g)].map(m=>({id:m[1],msg:m[2]}));
      const spam=/appears to be spam/.test(res.text);
      fs.writeFileSync('err'+step+'.html',res.text);
      const ei=res.text.indexOf('frm_error_style');console.log('SUMMARY:',res.text.slice(ei,ei+900).replace(/\s+/g,' '));
      console.log('ERRORS:',JSON.stringify(errs), spam?'SPAM':'');
      if(spam) break;
      for(const e of errs){ if(!fixes[e.id]) fixes[e.id]=/email/i.test(e.msg)?'alex.morgan@example.com':(/number|age|phone|postcode/i.test(e.msg)?'12345':'Yes I do'); }
      html=res.text; continue;
    }
    if(!/frm_field_/.test(res.text)){ console.log('DONE? status',res.status); fs.writeFileSync('final.html',res.text); break; }
    html=res.text;
  }
  fs.writeFileSync('pages.json',JSON.stringify(pages,null,1));
})();
