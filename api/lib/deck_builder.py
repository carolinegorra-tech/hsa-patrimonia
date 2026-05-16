const { useState, useRef, useEffect } = React;

const C = {
  bg: "#F4F4F2", surface: "#EBEBEA", card: "#FFFFFF",
  border: "#D8D8D6", borderLight: "#E4E4E2",
  gold: "#BF9447", goldBright: "#D4AA55", goldDim: "#8A6A2E",
  text: "#283944", muted: "#7E7F81", dim: "#AAAAAA",
  green: "#3CAE7A", red: "#E05252", blue: "#4A90D9",
};

const style = `
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Nunito+Sans:wght@300;400;600;700&display=swap');
  *{box-sizing:border-box;margin:0;padding:0}
  ::-webkit-scrollbar{width:5px;height:5px}
  ::-webkit-scrollbar-track{background:#F4F4F2}
  ::-webkit-scrollbar-thumb{background:#D8D8D6;border-radius:3px}
  .uz{transition:border-color .2s,background .2s,transform .1s}
  .uz:hover{border-color:#BF9447!important;background:rgba(191,148,71,.07)!important;transform:translateY(-2px)}
  .rh:hover{background:rgba(255,255,255,.025)!important}
  .bg{transition:all .2s}.bg:hover{background:#D4AA55!important;transform:translateY(-1px);box-shadow:0 6px 24px rgba(191,148,71,.35)!important}
  .gh{transition:all .2s}.gh:hover{border-color:#BF9447!important;color:#BF9447!important}
  @keyframes spin{to{transform:rotate(360deg)}}
  @keyframes fi{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
  .fi{animation:fi .35s ease forwards}
  @keyframes pu{0%,100%{opacity:.6}50%{opacity:1}}
  .pu{animation:pu 1.5s ease infinite}
`;

const brl = v => v != null && v !== "" ? new Intl.NumberFormat("pt-BR",{style:"currency",currency:"BRL",minimumFractionDigits:2,maximumFractionDigits:2}).format(v) : "—";
const usd = v => v > 0 ? "US$ "+new Intl.NumberFormat("pt-BR",{minimumFractionDigits:2,maximumFractionDigits:2}).format(v) : "—";
const n = v => v != null && v !== 0 ? new Intl.NumberFormat("pt-BR",{minimumFractionDigits:2,maximumFractionDigits:2}).format(v) : "—";

const DEMO = {
  client:"SÉRGIO COUTINHO GALVÃO FILHO", cpf:"***.***.***-**", year:2024,
  groups:[
    {name:"Imóveis",jurisdiction:"Brasil",items:[
      {id:3,desc:"Apartamento São Conrado",loc:"Rio de Janeiro, RJ",dirpf:11897122.05,dcbe:null},
      {id:9,desc:"Casa e terreno Pacaembu",loc:"São Paulo, SP",dirpf:7237937.02,dcbe:null},
      {id:12,desc:"Casa Quinta da Baronesa",loc:"Bragança Paulista, SP",dirpf:10990000,dcbe:null},
      {id:11,desc:"Casa Juquey",loc:"São Sebastião, SP",dirpf:6924403,dcbe:null},
    ]},
    {name:"Obras de Arte",jurisdiction:"Brasil",items:[
      {id:29,desc:"Quadro Grafisme en Noir et Rouge",loc:"Brasil",dirpf:4826178,dcbe:null},
      {id:33,desc:"Obra Relief 373",loc:"Brasil",dirpf:5284853.6,dcbe:null},
      {id:34,desc:"Obra Antonio Bandeira",loc:"Brasil",dirpf:4000000,dcbe:null},
    ]},
    {name:"Ações",jurisdiction:"Brasil",items:[
      {id:42,desc:"13.531.814 ações Raia Drogasil S.A.",loc:"Brasil",dirpf:27457756.33,dcbe:null},
      {id:41,desc:"100.540 ações Klabin S.A. (KLBN11)",loc:"Brasil",dirpf:3784445.22,dcbe:null},
    ]},
    {name:"Participações Societárias",jurisdiction:"Brasil",items:[
      {id:45,desc:"XXXXX Inv. e Part. Ltda.",loc:"Brasil",dirpf:125209973.97,dcbe:null},
      {id:46,desc:"XXXXXXX Holdings S.A.",loc:"Brasil",dirpf:29309104.88,dcbe:null},
      {id:44,desc:"XXXXX Investimentos Ltda.",loc:"Brasil",dirpf:11526046.5,dcbe:null},
    ]},
    {name:"Fundos de Investimento",jurisdiction:"Brasil",items:[
      {id:65,desc:"Araucária Investimento no Exterior FIM",loc:"Brasil",dirpf:28210793.95,dcbe:null},
      {id:70,desc:"Araucária Segundo FIA Ações",loc:"Brasil",dirpf:27328813.06,dcbe:null},
    ]},
    {name:"Investimentos Renda Fixa",jurisdiction:"Brasil",items:[
      {id:57,desc:"CDB Banco BTG Pactual S.A.",loc:"Brasil",dirpf:3752587.99,dcbe:null},
      {id:60,desc:"LCI XP Investimentos CCTVM S.A.",loc:"Brasil",dirpf:1372391.81,dcbe:null},
    ]},
    {name:"Contas Bancárias",jurisdiction:"Brasil",items:[
      {id:84,desc:"Conta Corrente Itaú Unibanco S.A.",loc:"Brasil",dirpf:529310.48,dcbe:null},
      {id:85,desc:"Conta Corrente Banco C6 S.A.",loc:"Brasil",dirpf:49453.46,dcbe:null},
    ]},
    {name:"Créditos",jurisdiction:"Brasil",items:[
      {id:88,desc:"Créditos a receber L Inv. e Part. EIRELI",loc:"Brasil",dirpf:2514810.4,dcbe:null},
      {id:53,desc:"AFAC L Galpões Investimentos Ltda.",loc:"Brasil",dirpf:1900000,dcbe:null},
    ]},
    {name:"Participações Societárias",jurisdiction:"Offshore",items:[
      {id:107,desc:"XXXXXXXX Ltd. (100%)",loc:"Bahamas",dirpf:44656048.98,dcbe:12188023},
      {id:104,desc:"XXXXXXXX Limited (100%)",loc:"Bahamas",dirpf:14633402.63,dcbe:9949412},
    ]},
    {name:"Contas Bancárias",jurisdiction:"Offshore",items:[
      {id:116,desc:"Conta Corrente e Poupança Santander Totta",loc:"Portugal",dirpf:6700188.3,dcbe:1041000},
      {id:113,desc:"Conta Corrente JP Morgan Chase Bank (EUR)",loc:"EUA",dirpf:1769145.78,dcbe:274870},
    ]},
    {name:"Seguros de Vida",jurisdiction:"Offshore",items:[
      {id:118,desc:"Seguro de vida Zurich Life Insurance (1)",loc:"Suíça",dirpf:929670,dcbe:350000},
      {id:119,desc:"Seguro de vida Zurich Life Insurance (2)",loc:"Suíça",dirpf:929670,dcbe:350000},
    ]},
  ],
};

function EditCell({value, onChange}) {
  const [editing, setEditing] = useState(false);
  const [raw, setRaw] = useState("");
  if (editing) return (
    <input autoFocus value={raw}
      onChange={e=>setRaw(e.target.value)}
      onBlur={()=>{const v=parseFloat(raw.replace(/\./g,"").replace(",","."));if(!isNaN(v))onChange(v);setEditing(false);}}
      onKeyDown={e=>{if(e.key==="Enter"){const v=parseFloat(raw.replace(/\./g,"").replace(",","."));if(!isNaN(v))onChange(v);setEditing(false);}if(e.key==="Escape")setEditing(false);}}
      style={{width:"100%",background:C.surface,border:`1px solid ${C.gold}`,borderRadius:4,color:C.text,fontFamily:"monospace",fontSize:11,padding:"3px 6px",textAlign:"right"}}
    />
  );
  return (
    <span onClick={()=>{setRaw(value!=null?String(value):"");setEditing(true);}}
      title="Clique para editar"
      style={{cursor:"pointer",borderBottom:`1px dashed ${C.dim}`,display:"inline-block",minWidth:60,textAlign:"right"}}>
      {value!=null?n(value):"—"}
    </span>
  );
}

function GroupTable({group, onUpdate}){
  const [open,setOpen]=useState(true);
  const totD=group.items.reduce((a,i)=>a+(i.dirpf||0),0);
  const totC=group.items.reduce((a,i)=>a+(i.dcbe||0),0);
  return(
    <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:10,marginBottom:10,overflow:"hidden"}}>
      <div onClick={()=>setOpen(!open)} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"14px 18px",cursor:"pointer",userSelect:"none"}}>
        <div style={{display:"flex",alignItems:"center",gap:10}}>
          <span style={{fontWeight:700,fontSize:13,color:C.text}}>{group.name}</span>
          <span style={{background:C.surface,color:C.muted,fontSize:10,padding:"2px 8px",borderRadius:20}}>{group.items.length} {group.items.length===1?"item":"itens"}</span>
        </div>
        <div style={{display:"flex",alignItems:"center",gap:20}}>
          <span style={{fontFamily:"'Cormorant Garamond',serif",fontSize:17,fontWeight:600,color:C.goldBright}}>{brl(totD)}</span>
          {totC>0&&<span style={{fontSize:11,color:C.gold}}>{usd(totC)}</span>}
          <span style={{color:C.dim,fontSize:10}}>{open?"▲":"▼"}</span>
        </div>
      </div>
      {open&&(
        <div style={{overflowX:"auto"}}>
          <div style={{padding:"4px 18px 6px",background:C.surface,borderTop:`1px solid ${C.border}`}}>
            <span style={{fontSize:10,color:C.dim}}>✏️ Clique em qualquer valor para editar</span>
          </div>
          <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
            <thead>
              <tr style={{background:C.surface}}>
                {["#","Descrição","País / Local","DIRPF (R$)","DCBE (US$)"].map((h,i)=>(
                  <th key={h} style={{padding:"7px 12px",color:C.muted,fontWeight:600,fontSize:10,letterSpacing:"0.08em",textTransform:"uppercase",textAlign:i>=3?"right":i===0?"center":"left",whiteSpace:"nowrap"}}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {group.items.map((item,idx)=>(
                <tr key={item.id||idx} className="rh" style={{borderTop:`1px solid ${C.border}`}}>
                  <td style={{padding:"9px 12px",color:C.muted,textAlign:"center",fontSize:10}}>{item.id}</td>
                  <td style={{padding:"9px 12px",color:C.text,maxWidth:340}}>{item.desc}</td>
                  <td style={{padding:"9px 12px",color:C.muted,whiteSpace:"nowrap"}}>{item.loc}</td>
                  <td style={{padding:"9px 12px",textAlign:"right",fontFamily:"monospace",fontSize:11,color:C.text}}>
                    <EditCell value={item.dirpf} onChange={v=>onUpdate(group.name,group.jurisdiction,idx,"dirpf",v)}/>
                  </td>
                  <td style={{padding:"9px 12px",textAlign:"right",fontFamily:"monospace",fontSize:11,color:item.dcbe>0?C.goldBright:C.dim}}>
                    <EditCell value={item.dcbe>0?item.dcbe:null} onChange={v=>onUpdate(group.name,group.jurisdiction,idx,"dcbe",v)}/>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr style={{background:C.surface,borderTop:`1px solid ${C.borderLight}`}}>
                <td colSpan={3} style={{padding:"9px 12px",color:C.muted,fontSize:10,fontWeight:700,letterSpacing:"0.1em"}}>SUBTOTAL</td>
                <td style={{padding:"9px 12px",color:C.goldBright,textAlign:"right",fontFamily:"monospace",fontWeight:700,fontSize:12}}>{n(totD)}</td>
                <td style={{padding:"9px 12px",color:C.goldBright,textAlign:"right",fontFamily:"monospace",fontWeight:700,fontSize:11}}>{totC>0?n(totC):"—"}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  );
}

function App(){
  const [step,setStep]=useState("auth-check");
  const [files,setFiles]=useState({dirpf:null,dcbe:null});
  const [data,setData]=useState(null);
  const [loading,setLoading]=useState(false);
  const [loadMsg,setLoadMsg]=useState("");
  const [error,setError]=useState("");
  const [password,setPassword]=useState(()=>sessionStorage.getItem("hsa_pwd")||"");
  const [authRequired,setAuthRequired]=useState(false);
  const [pendingPwd,setPendingPwd]=useState("");
  const dirpfRef=useRef();
  const dcbeRef=useRef();

  // On mount: probe /api/health to learn if auth is required
  useEffect(()=>{
    fetch("/api/health").then(r=>r.json()).then(h=>{
      const needs = !!h.auth_enabled;
      setAuthRequired(needs);
      if (needs && !password) setStep("login");
      else setStep("upload");
    }).catch(()=>{ setStep("upload"); });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  },[]);

  const authHeaders = () => password ? {"X-HSA-Password": password} : {};

  const tryLogin = async () => {
    setError("");
    // Probe an authed endpoint with the candidate password
    const r = await fetch("/api/build/deck",{
      method:"POST",
      headers:{"Content-Type":"application/json","X-HSA-Password":pendingPwd},
      body: JSON.stringify({client:"_probe_",groups:[]})
    });
    if (r.status === 401) { setError("Senha incorreta."); return; }
    // Anything other than 401 means the password was accepted (even a 400/500 from empty data)
    sessionStorage.setItem("hsa_pwd", pendingPwd);
    setPassword(pendingPwd);
    setPendingPwd("");
    setStep("upload");
  };

  const toB64=f=>new Promise((res,rej)=>{const r=new FileReader();r.onload=()=>res(r.result.split(",")[1]);r.onerror=rej;r.readAsDataURL(f);});

  const processFiles=async()=>{
    if(!files.dirpf&&!files.dcbe)return;
    setLoading(true);setError("");
    try{
      const fd = new FormData();
      if(files.dirpf){setLoadMsg("Enviando DIRPF...");fd.append("dirpf", files.dirpf);}
      if(files.dcbe){setLoadMsg("Enviando DCBE...");fd.append("dcbe", files.dcbe);}
      setLoadMsg("Extraindo dados com IA...");
      let res;
      try{
        res = await fetch("/api/extract",{method:"POST", body:fd, headers: authHeaders()});
      } catch(e){ throw new Error("Falha na requisição: "+e.message); }
      if(res.status === 401){
        sessionStorage.removeItem("hsa_pwd"); setPassword(""); setStep("login");
        throw new Error("Sessão expirada. Faça login novamente.");
      }
      const body = await res.text();
      if(!res.ok){
        let msg = body;
        try { msg = JSON.parse(body).detail || body; } catch {}
        throw new Error(`API HTTP ${res.status}: ${String(msg).slice(0,260)}`);
      }
      let parsed;
      try{ parsed = JSON.parse(body); }
      catch(e){ throw new Error("JSON inválido do backend: "+body.slice(0,150)); }
      setData(parsed);setStep("verify");
    }catch(e){setError(e.message);}
    finally{setLoading(false);setLoadMsg("");}
  };

  const [downloadStatus, setDownloadStatus] = useState({});
  const [downloadingKind, setDownloadingKind] = useState(null);

  const KIND_TO_URL = {
    excel:           "/api/build/excel",
    deck:            "/api/build/deck",
    orgPatrimonial:  "/api/build/orgchart-patrimonial",
    orgFamiliar:     "/api/build/orgchart-familiar",
  };
  const KIND_FALLBACK_NAME = {
    excel:          "lista_ativos.xlsx",
    deck:           "patrimonio.pptx",
    orgPatrimonial: "organograma_patrimonial.pptx",
    orgFamiliar:    "organograma_familiar.pptx",
  };

  const downloadOne = async (kind) => {
    setDownloadingKind(kind); setError("");
    try {
      const r = await fetch(KIND_TO_URL[kind], {
        method: "POST",
        headers: {"Content-Type":"application/json", ...authHeaders()},
        body: JSON.stringify(data),
      });
      if (!r.ok) {
        const t = await r.text();
        let msg = t; try { msg = JSON.parse(t).detail || t; } catch {}
        throw new Error(`Falha ao gerar ${kind}: ${String(msg).slice(0,240)}`);
      }
      const cd = r.headers.get("content-disposition") || "";
      const m = /filename="?([^";]+)"?/i.exec(cd);
      const fname = m ? m[1] : KIND_FALLBACK_NAME[kind];
      const blob = await r.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = fname;
      document.body.appendChild(link); link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
      setDownloadStatus(s => ({...s, [kind]: fname}));
      return fname;
    } catch (e) {
      setError(e.message);
    } finally {
      setDownloadingKind(null);
    }
  };

  const confirm = () => {
    setError("");
    setDownloadStatus({});
    setStep("done");
  };

  const updateItem = (grpName, juris, idx, field, value) => {
    setData(prev => {
      const groups = prev.groups.map(g => {
        if (g.name === grpName && g.jurisdiction === juris) {
          const items = g.items.map((it, i) => i === idx ? {...it, [field]: value} : it);
          return {...g, items};
        }
        return g;
      });
      return {...prev, groups};
    });
  };

  const totDIRPF=data?.groups?.reduce((a,g)=>a+g.items.reduce((b,i)=>b+(i.dirpf||0),0),0)||0;
  const totDCBE=data?.groups?.reduce((a,g)=>a+g.items.reduce((b,i)=>b+(i.dcbe||0),0),0)||0;
  const nItems=data?.groups?.reduce((a,g)=>a+g.items.length,0)||0;
  const brGrps=data?.groups?.filter(g=>g.jurisdiction==="Brasil")||[];
  const offGrps=data?.groups?.filter(g=>g.jurisdiction==="Offshore")||[];

  if(step==="upload")return(
    <div style={{background:C.bg,minHeight:"100vh",fontFamily:"'Nunito Sans',sans-serif",color:C.text,display:"flex",alignItems:"center",justifyContent:"center",padding:"32px 20px"}}>
      <style>{style}</style>
      <div style={{width:"100%",maxWidth:640}}>
        <div style={{textAlign:"center",marginBottom:32}}>
          <div style={{display:"inline-flex",alignItems:"center",gap:8,background:C.surface,border:`1px solid ${C.border}`,borderRadius:20,padding:"5px 16px",marginBottom:20}}>
            <div style={{width:5,height:5,borderRadius:"50%",background:C.gold}} className="pu"/>
            <span style={{color:C.muted,fontSize:10,letterSpacing:"0.2em",fontWeight:700}}>PATRIMÔNIO FAMILIAR · CONFIDENCIAL</span>
          </div>
          <h1 style={{fontFamily:"'Cormorant Garamond',serif",fontSize:38,fontWeight:600,color:C.text,lineHeight:1.1}}>Gerador de<br/><span style={{color:C.gold,fontStyle:"italic"}}>Relatório Patrimonial</span></h1>
          <p style={{color:C.muted,fontSize:13,marginTop:10,lineHeight:1.6}}>Carregue os arquivos da DIRPF e DCBE do cliente para extrair, verificar e gerar os relatórios.</p>
        </div>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14,marginBottom:16}}>
          {[{key:"dirpf",ref:dirpfRef,icon:"📋",label:"DIRPF 2025",sub:"Declaração de Imposto de Renda",badge:"Receita Federal"},{key:"dcbe",ref:dcbeRef,icon:"🌐",label:"DCBE 2025",sub:"Capitais Brasileiros no Exterior",badge:"Banco Central"}].map(({key,ref,icon,label,sub,badge})=>(
            <div key={key} className="uz" onClick={()=>ref.current?.click()} style={{background:files[key]?"rgba(191,148,71,.06)":C.card,border:`1.5px dashed ${files[key]?C.gold:C.border}`,borderRadius:12,padding:"28px 20px",textAlign:"center",cursor:"pointer"}}>
              <input ref={ref} type="file" accept=".pdf" style={{display:"none"}} onChange={e=>setFiles(p=>({...p,[key]:e.target.files[0]}))}/>
              <div style={{fontSize:32,marginBottom:12}}>{files[key]?"✅":icon}</div>
              <div style={{fontWeight:700,fontSize:14,color:files[key]?C.goldBright:C.text,marginBottom:3}}>{label}</div>
              <div style={{color:C.muted,fontSize:11,marginBottom:8}}>{files[key]?files[key].name:sub}</div>
              <div style={{display:"inline-block",background:C.surface,border:`1px solid ${C.border}`,borderRadius:20,padding:"2px 8px",color:C.dim,fontSize:9,letterSpacing:"0.1em",fontWeight:700}}>{badge}</div>
            </div>
          ))}
        </div>
        {error&&<div style={{background:"rgba(224,82,82,.1)",border:`1px solid ${C.red}`,borderRadius:8,padding:"12px 16px",color:C.red,fontSize:12,marginBottom:14}}>⚠ {error}</div>}
        <div style={{display:"flex",gap:12,justifyContent:"center",marginBottom:20}}>
          <button className="bg" style={{background:C.gold,color:"#080C14",padding:"13px 30px",borderRadius:8,border:"none",cursor:(files.dirpf||files.dcbe)&&!loading?"pointer":"not-allowed",fontFamily:"'Nunito Sans',sans-serif",fontWeight:700,fontSize:14,letterSpacing:"0.05em",opacity:(files.dirpf||files.dcbe)&&!loading?1:0.4}} onClick={processFiles}>
            {loading?<span style={{display:"flex",alignItems:"center",gap:8}}><span style={{width:13,height:13,border:"2px solid rgba(0,0,0,.3)",borderTopColor:"#000",borderRadius:"50%",animation:"spin .8s linear infinite",display:"inline-block"}}/>{loadMsg||"Processando..."}</span>:"→ Processar Arquivos PDF"}
          </button>
          <button className="gh" style={{background:"transparent",color:C.muted,padding:"13px 22px",borderRadius:8,border:`1px solid ${C.border}`,cursor:"pointer",fontFamily:"'Nunito Sans',sans-serif",fontSize:13}} onClick={()=>{setData(DEMO);setStep("verify");}}>Usar Dados Demo</button>
        </div>
        <p style={{textAlign:"center",color:C.dim,fontSize:11,lineHeight:1.6}}>Os documentos são processados via API e não são armazenados.<br/>Também é possível carregar apenas um dos dois arquivos.</p>
      </div>
    </div>
  );

  if(step==="verify")return(
    <div style={{background:C.bg,minHeight:"100vh",fontFamily:"'Nunito Sans',sans-serif",color:C.text,padding:"24px 20px"}} className="fi">
      <style>{style}</style>
      <div style={{maxWidth:980,margin:"0 auto"}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:24,flexWrap:"wrap",gap:12}}>
          <div>
            <p style={{color:C.muted,fontSize:10,fontWeight:700,letterSpacing:"0.2em",marginBottom:4}}>VERIFICAÇÃO DOS DADOS · CONFIDENCIAL</p>
            <h1 style={{fontFamily:"'Cormorant Garamond',serif",fontSize:28,fontWeight:600,color:C.text}}>{data?.client||"—"}</h1>
            <p style={{color:C.muted,fontSize:12,marginTop:2}}>Ano-calendário {data?.year} · {data?.groups?.length} categorias · {nItems} itens · <span style={{color:C.dim,fontSize:11}}>⚿ dados anonimizados</span></p>
          </div>
          <div style={{display:"flex",gap:10,alignItems:"center"}}>
            <button className="gh" style={{background:"transparent",color:C.muted,padding:"10px 18px",borderRadius:8,border:`1px solid ${C.border}`,cursor:"pointer",fontFamily:"'Nunito Sans',sans-serif",fontSize:12}} onClick={()=>setStep("upload")}>← Voltar</button>
            <button className="bg" style={{background:C.gold,color:"#080C14",padding:"10px 22px",borderRadius:8,border:"none",cursor:"pointer",fontFamily:"'Nunito Sans',sans-serif",fontWeight:700,fontSize:13,letterSpacing:"0.04em"}} onClick={confirm}>✓ Confirmar e Gerar Excel + PPT</button>
          </div>
        </div>
        <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:10,marginBottom:16}}>
          {[{label:"Total DIRPF",value:brl(totDIRPF),accent:C.text},{label:"Total DCBE (Offshore)",value:(()=>{const t=data?.groups?.filter(g=>g.jurisdiction==="Offshore")?.reduce((a,g)=>a+g.items.reduce((b,i)=>b+(i.dcbe||0),0),0)||0; return t>0?usd(t):"N/A";})(),accent:C.gold},{label:"Ativos Brasil",value:brGrps.reduce((a,g)=>a+g.items.length,0)+" itens",accent:C.green},{label:"Ativos Offshore",value:offGrps.reduce((a,g)=>a+g.items.length,0)+" itens",accent:C.blue}].map(({label,value,accent})=>(
            <div key={label} style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:10,padding:"14px 16px"}}>
              <p style={{color:C.muted,fontSize:9,fontWeight:700,letterSpacing:"0.15em",marginBottom:6}}>{label}</p>
              <p style={{fontFamily:"'Cormorant Garamond',serif",fontSize:20,fontWeight:600,color:accent}}>{value}</p>
            </div>
          ))}
        </div>

        {/* Family info row */}
        {(data?.spouse?.name || (data?.dependents?.length > 0)) && (
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:16}}>
            {data?.spouse?.name && (
              <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:10,padding:"14px 16px"}}>
                <p style={{color:C.muted,fontSize:9,fontWeight:700,letterSpacing:"0.15em",marginBottom:6}}>CÔNJUGE / COMPANHEIRO(A)</p>
                <p style={{fontSize:13,fontWeight:600,color:C.text,marginBottom:2}}>{data.spouse.name}</p>
                <p style={{color:C.muted,fontSize:11}}>{data.spouse.marriage_regime || "Regime não informado"}{data.spouse.marriage_date ? " · " + data.spouse.marriage_date : ""}</p>
                {data.spouse.certificate_registry && <p style={{color:C.muted,fontSize:10,marginTop:2}}>{data.spouse.certificate_registry}</p>}
              </div>
            )}
            {data?.dependents?.length > 0 && (
              <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:10,padding:"14px 16px"}}>
                <p style={{color:C.muted,fontSize:9,fontWeight:700,letterSpacing:"0.15em",marginBottom:6}}>DEPENDENTES ({data.dependents.length})</p>
                {data.dependents.map((d,i) => (
                  <p key={i} style={{fontSize:12,color:C.text,marginBottom:2}}>{d.name} <span style={{color:C.muted,fontSize:10}}>— {d.relationship}</span></p>
                ))}
              </div>
            )}
          </div>
        )}
        {brGrps.length>0&&(
          <div style={{marginBottom:20}}>
            <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:12}}>
              <div style={{width:3,height:14,background:C.green,borderRadius:2}}/>
              <span style={{color:C.green,fontWeight:700,fontSize:11,letterSpacing:"0.15em"}}>BRASIL</span>
              <span style={{color:C.muted,fontSize:11}}>{brl(brGrps.reduce((a,g)=>a+g.items.reduce((b,i)=>b+(i.dirpf||0),0),0))}</span>
            </div>
            {brGrps.map(g=><GroupTable key={g.name+g.jurisdiction} group={g} onUpdate={updateItem}/>)}
          </div>
        )}
        {offGrps.length>0&&(
          <div style={{marginBottom:24}}>
            <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:12}}>
              <div style={{width:3,height:14,background:C.gold,borderRadius:2}}/>
              <span style={{color:C.gold,fontWeight:700,fontSize:11,letterSpacing:"0.15em"}}>OFFSHORE</span>
              <span style={{color:C.muted,fontSize:11}}>{brl(offGrps.reduce((a,g)=>a+g.items.reduce((b,i)=>b+(i.dirpf||0),0),0))}</span>
            </div>
            {offGrps.map(g=><GroupTable key={g.name+g.jurisdiction} group={g} onUpdate={updateItem}/>)}
          </div>
        )}
        <div style={{background:C.card,border:`1px solid ${C.borderLight}`,borderRadius:10,padding:"16px 20px",display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:24}}>
          <span style={{fontWeight:700,fontSize:13,color:C.muted,letterSpacing:"0.1em"}}>TOTAL GERAL</span>
          <div style={{display:"flex",gap:24,alignItems:"center"}}>
            {totDCBE>0&&<span style={{color:C.gold,fontSize:14,fontFamily:"'Cormorant Garamond',serif",fontWeight:600}}>{usd(totDCBE)}</span>}
            <span style={{color:C.text,fontSize:22,fontFamily:"'Cormorant Garamond',serif",fontWeight:700}}>{brl(totDIRPF)}</span>
          </div>
        </div>
        {error&&<div style={{background:"rgba(224,82,82,.1)",border:`1px solid ${C.red}`,borderRadius:8,padding:"12px 16px",color:C.red,fontSize:12,marginBottom:14}}>⚠ {error}</div>}
        <div style={{textAlign:"center",paddingBottom:32}}>
          <button className="bg" style={{background:C.gold,color:"#080C14",padding:"15px 44px",borderRadius:10,border:"none",cursor:"pointer",fontFamily:"'Nunito Sans',sans-serif",fontWeight:700,fontSize:15,letterSpacing:"0.04em"}} onClick={confirm}>✓ Confirmar e Gerar Excel + PPT</button>
          <p style={{color:C.dim,fontSize:11,marginTop:10}}>Os arquivos são gerados no chat após confirmação</p>
        </div>
      </div>
    </div>
  );

  if(step==="auth-check") return (
    <div style={{background:C.bg,minHeight:"100vh",display:"flex",alignItems:"center",justifyContent:"center"}}>
      <p style={{color:C.muted,fontSize:12}}>Carregando...</p>
    </div>
  );

  if(step==="login") return (
    <div style={{background:C.bg,minHeight:"100vh",fontFamily:"'Nunito Sans',sans-serif",color:C.text,display:"flex",alignItems:"center",justifyContent:"center",padding:"32px 20px"}}>
      <style>{style}</style>
      <div style={{width:"100%",maxWidth:380}}>
        <div style={{textAlign:"center",marginBottom:28}}>
          <div style={{display:"inline-flex",alignItems:"center",gap:8,background:C.surface,border:`1px solid ${C.border}`,borderRadius:20,padding:"5px 16px",marginBottom:18}}>
            <div style={{width:5,height:5,borderRadius:"50%",background:C.gold}} className="pu"/>
            <span style={{color:C.muted,fontSize:10,letterSpacing:"0.2em",fontWeight:700}}>HSA ADVOGADOS · ACESSO RESTRITO</span>
          </div>
          <h1 style={{fontFamily:"'Cormorant Garamond',serif",fontSize:32,fontWeight:600,color:C.text,lineHeight:1.1}}>
            <span style={{color:C.gold,fontStyle:"italic"}}>Patrimon.IA</span>
          </h1>
          <p style={{color:C.muted,fontSize:12,marginTop:10}}>Insira a senha do escritório para continuar.</p>
        </div>
        <input
          type="password" autoFocus
          value={pendingPwd}
          onChange={e=>setPendingPwd(e.target.value)}
          onKeyDown={e=>{if(e.key==="Enter")tryLogin();}}
          placeholder="Senha"
          style={{width:"100%",background:C.card,border:`1px solid ${C.border}`,borderRadius:8,padding:"13px 16px",color:C.text,fontSize:14,marginBottom:12,fontFamily:"'Nunito Sans',sans-serif"}}
        />
        {error&&<div style={{background:"rgba(224,82,82,.1)",border:`1px solid ${C.red}`,borderRadius:8,padding:"10px 14px",color:C.red,fontSize:12,marginBottom:12}}>⚠ {error}</div>}
        <button className="bg" onClick={tryLogin}
          style={{width:"100%",background:C.gold,color:"#080C14",padding:"13px 30px",borderRadius:8,border:"none",cursor:"pointer",fontFamily:"'Nunito Sans',sans-serif",fontWeight:700,fontSize:14,letterSpacing:"0.05em"}}>
          Entrar →
        </button>
      </div>
    </div>
  );

  if(step==="done")return(
    <div style={{background:C.bg,minHeight:"100vh",fontFamily:"'Nunito Sans',sans-serif",color:C.text,display:"flex",alignItems:"center",justifyContent:"center",padding:"32px 20px"}} className="fi">
      <style>{style}</style>
      <div style={{width:"100%",maxWidth:720,textAlign:"center"}}>
        <div style={{fontSize:48,marginBottom:12}}>📥</div>
        <h2 style={{fontFamily:"'Cormorant Garamond',serif",fontSize:30,fontWeight:600,color:C.text,marginBottom:8}}>Arquivos disponíveis</h2>
        <p style={{color:C.muted,fontSize:13,lineHeight:1.7,marginBottom:24}}>
          Clique em cada arquivo para baixar. Você pode baixar quantas vezes precisar.
        </p>

        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14,marginBottom:24}}>
          {[
            {kind:"excel",          icon:"📊", title:"Lista de Ativos",          sub:"Excel completo (.xlsx)"},
            {kind:"orgPatrimonial", icon:"🏛️", title:"Organograma Patrimonial",  sub:"Slide isolado (.pptx)"},
            {kind:"orgFamiliar",    icon:"👨‍👩‍👧‍👦", title:"Organograma Familiar",     sub:"Slide isolado (.pptx)"},
            {kind:"deck",           icon:"📑", title:"Apresentação PPT",         sub:"6 slides — capa, composição, detalhamento, organogramas"},
          ].map(({kind,icon,title,sub}) => {
            const isDownloading = downloadingKind === kind;
            const wasDownloaded = !!downloadStatus[kind];
            return (
              <button key={kind} className="bg"
                disabled={isDownloading}
                onClick={()=>downloadOne(kind)}
                style={{
                  background: wasDownloaded ? "rgba(60,174,122,.06)" : C.card,
                  color: C.text,
                  padding: "22px 18px",
                  borderRadius: 12,
                  border: `1.5px solid ${wasDownloaded ? C.green : C.border}`,
                  cursor: isDownloading ? "wait" : "pointer",
                  fontFamily: "'Nunito Sans',sans-serif",
                  fontSize: 13,
                  fontWeight: 600,
                  textAlign: "left",
                  minHeight: 140,
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  opacity: isDownloading ? 0.6 : 1,
                }}>
                <div>
                  <div style={{fontSize:28,marginBottom:10}}>{icon}</div>
                  <div style={{color:C.text,marginBottom:4,fontSize:14}}>{title}</div>
                  <div style={{color:C.muted,fontSize:11,fontWeight:400,lineHeight:1.5}}>{sub}</div>
                </div>
                <div style={{marginTop:10,fontSize:11,fontWeight:700,letterSpacing:"0.05em"}}>
                  {isDownloading ? (
                    <span style={{color:C.gold}}>
                      <span style={{display:"inline-block",width:10,height:10,border:"2px solid rgba(191,148,71,.3)",borderTopColor:C.gold,borderRadius:"50%",animation:"spin .8s linear infinite",marginRight:6,verticalAlign:"middle"}}/>
                      Gerando...
                    </span>
                  ) : wasDownloaded ? (
                    <span style={{color:C.green}}>✓ Baixado</span>
                  ) : (
                    <span style={{color:C.gold}}>↓ Baixar</span>
                  )}
                </div>
              </button>
            );
          })}
        </div>

        <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:12,padding:"14px 20px",marginBottom:20,textAlign:"left"}}>
          <p style={{color:C.muted,fontSize:10,fontWeight:700,letterSpacing:"0.15em",marginBottom:4}}>CLIENTE</p>
          <p style={{fontFamily:"'Cormorant Garamond',serif",fontSize:17,fontWeight:600,color:C.text}}>{data?.client||"—"}</p>
          <p style={{color:C.muted,fontSize:11,marginTop:2}}>
            {data?.year} · {data?.groups?.reduce((a,g)=>a+g.items.length,0)} ativos ·{" "}
            {new Intl.NumberFormat("pt-BR",{style:"currency",currency:"BRL",minimumFractionDigits:2,maximumFractionDigits:2}).format(data?.groups?.reduce((a,g)=>a+g.items.reduce((b,i)=>b+(i.dirpf||0),0),0)||0)}
          </p>
        </div>

        {error&&<div style={{background:"rgba(224,82,82,.1)",border:`1px solid ${C.red}`,borderRadius:8,padding:"10px 14px",color:C.red,fontSize:12,marginBottom:16,textAlign:"left"}}>⚠ {error}</div>}

        <div style={{display:"flex",gap:10,justifyContent:"center"}}>
          <button className="gh" style={{background:"transparent",color:C.muted,padding:"11px 24px",borderRadius:8,border:`1px solid ${C.border}`,cursor:"pointer",fontFamily:"'Nunito Sans',sans-serif",fontSize:13}} onClick={()=>setStep("verify")}>← Voltar para verificação</button>
          <button className="gh" style={{background:"transparent",color:C.muted,padding:"11px 24px",borderRadius:8,border:`1px solid ${C.border}`,cursor:"pointer",fontFamily:"'Nunito Sans',sans-serif",fontSize:13}} onClick={()=>{setStep("upload");setData(null);setFiles({dirpf:null,dcbe:null});setError("");setDownloadStatus({});}}>Novo Cliente</button>
        </div>
      </div>
    </div>
  );

  return null;
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
