export const $=s=>document.querySelector(s);
export function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n}
export function button(text,fn){const b=el('button',text);b.type='button';b.onclick=fn;return b}
export const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback}catch{return fallback}};
export const save=(key,value)=>{try{localStorage.setItem(key,JSON.stringify(value))}catch{}};
export function paragraphs(parent,text){String(text||'').split('\n').forEach(line=>{if(!line.trim())return;parent.append(el(line.startsWith('- ')?'li':'p',line.replace(/^- /,'')))})}
export function shuffled(items){const result=[...items];for(let i=result.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[result[i],result[j]]=[result[j],result[i]]}return result}
