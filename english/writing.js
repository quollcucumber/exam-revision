await import('../assets/subject.js');
const headings=new Set(['Antigone','Ismene','Creon','Haemon','Chorus','Sentry','Teiresias','Later scenes (no speaker given on your sheet)']);
document.querySelectorAll('.note:first-of-type p').forEach(p=>{if(headings.has(p.textContent)){const h=document.createElement('h3');h.textContent=p.textContent;p.replaceWith(h)}});
