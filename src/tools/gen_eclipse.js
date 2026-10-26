// 从 stonelf/zangli 的 data/eclipse-list.js 取出范围内的日月食（北京时间）：node gen_eclipse.js <eclipse-list.js 路径>
const el=require(process.argv[2]);const t0=Date.UTC(2025,11,1),t1=Date.UTC(2037,3,1),H8=8*36e5;
const bj=t=>{const x=new Date(t+H8);return x.getUTCHours()+':'+String(x.getUTCMinutes()).padStart(2,'0')};
const out=el.eclipseList.filter(e=>e[0]>=t0&&e[0]<t1).map(e=>{const x=new Date(e[0]+H8);const jd=Math.floor(Date.UTC(x.getUTCFullYear(),x.getUTCMonth(),x.getUTCDate())/864e5)+2440588;
  return [jd,el.eclipseType[e[1]],bj(e[0]),e.length>2?bj(e[2]):'',e.length>2?bj(e[3]):'']});
console.log(JSON.stringify(out));
