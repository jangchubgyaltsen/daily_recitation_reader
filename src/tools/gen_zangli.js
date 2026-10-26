// 用 stonelf/zangli 生成藏历月表：TZ=Asia/Shanghai node gen_zangli.js <zangli.js 路径> <输出 json>
const z=require(process.argv[2]||'./zangli/zangli.js');
const DN=["初一","初二","初三","初四","初五","初六","初七","初八","初九","初十","十一","十二","十三","十四","十五","十六","十七","十八","十九","二十","廿一","廿二","廿三","廿四","廿五","廿六","廿七","廿八","廿九","三十"];
const MN=["正","二","三","四","五","六","七","八","九","十","十一","十二"];
const months=[];let cur=null;
// 从 2026 年藏历新年前的那个月开始，到 2037 年初
for(let t=Date.UTC(2025,11,1);t<=Date.UTC(2037,2,31);t+=864e5){const g=new Date(t);
  const r=z.getZangli(new Date(g.getUTCFullYear(),g.getUTCMonth(),g.getUTCDate()));
  const jd=Math.round(t/864e5)+2440588;const key=r.year+r.month;
  const d=DN.indexOf(r.day.replace('闰',''))+1;
  if(!cur||cur.key!==key){cur={key,year:r.year,M:MN.indexOf(r.month.replace('闰',''))+1,leap:r.monthLeap,jd0:jd,days:[]};months.push(cur)}
  cur.days.push(r.dayLeap?-d:d)}
months.shift();months.pop(); // 去掉首尾不完整的月
console.log(JSON.stringify(months.slice(0,3).map(m=>[m.year,m.M,m.leap,m.jd0,m.days.join(',')])));
console.log(months.length, months[0].key, months.at(-1).key);
console.log(months.filter(m=>m.leap).map(m=>m.key+' '+new Date((m.jd0-2440588)*864e5).toISOString().slice(0,10)));
require('fs').writeFileSync(process.argv[3]||'zl-months.json',JSON.stringify(months));
