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

// ── Persistent review storage ────────────────────────────────────────────
// Each client has a single JSON blob in localStorage with shape:
//   { "normalized desc 1": {reviewed:true, comments:"..."}, ... }
// Normalization is aggressive (alphanumeric only) so small variations in the
// AI's extracted text (spacing, punctuation, accents) still match the same key.
const normalizeKey = (s) => (s||"")
  .toString()
  .normalize("NFD")
  .replace(/[\u0300-\u036f]/g,"")  // strip accents
  .toLowerCase()
  .replace(/[^a-z0-9]/g,"")        // alphanumeric only — max stability
  .slice(0,100);

const reviewStoreKey = (client) => `clientReview:${normalizeKey(client)}`;

const loadReviewStore = (client) => {
  try {
    const raw = localStorage.getItem(reviewStoreKey(client));
    return raw ? JSON.parse(raw) : {};
  } catch(e) { return {}; }
};

const saveReviewStore = (client, store) => {
  try { localStorage.setItem(reviewStoreKey(client), JSON.stringify(store)); }
  catch(e) {}
};

const hydrateItemsFromStore = (groups, client) => {
  const store = loadReviewStore(client);
  return groups.map(g => ({
    ...g,
    items: g.items.map(item => {
      const k = normalizeKey(item.desc);
      const saved = store[k];
      // Always wipe whatever comment the AI put in `comments` — comments should
      // ONLY come from the user typing in the textarea (saved in localStorage).
      return {
        ...item,
        comments: saved?.comments || "",
        reviewed: saved?.reviewed || false,
      };
    }),
  }));
};


const DEMO = {
  client:"JANE MARGARET DOE", year:2024,
  spouse:{name:"JOHN ROBERT DOE", marriage_regime:"Comunhão Parcial de Bens", marriage_date:"08/04/2003"},
  dependents:[
    {name:"OLIVIA MARIA DOE", birth_date:"12/09/2006", relationship:"Filha(o)"},
    {name:"LUCAS HENRIQUE DOE", birth_date:"27/04/2010", relationship:"Filha(o)"},
  ],
  groups:[
    {name:"Bens Imóveis", jurisdiction:"Brasil", items:[
      {id:1, desc:"Apartamento 280m² Rua dos Pinheiros 1428 ap 502", loc:"São Paulo, SP", dirpf:9200000, dcbe:null, comments:""},
      {id:2, desc:"Casa de campo 450m² Itu SP", loc:"Itu, SP", dirpf:2480000, dcbe:null, comments:""},
      {id:3, desc:"Apartamento 95m² Copacabana", loc:"Rio de Janeiro, RJ", dirpf:1500000, dcbe:null, comments:""},
    ]},
    {name:"Bens Móveis / Obras de Arte", jurisdiction:"Brasil", items:[
      {id:4, desc:"Veículos e joias", loc:"Brasil", dirpf:1840000, dcbe:null, comments:""},
    ]},
    {name:"Participações Societárias", jurisdiction:"Brasil", items:[
      {id:5, desc:"Cotas empresa operacional", loc:"Brasil", dirpf:45220000, dcbe:null, comments:""},
    ]},
    {name:"Aplicações e Investimentos", jurisdiction:"Brasil", items:[
      {id:6, desc:"CDB / Fundos / Renda Fixa", loc:"Brasil", dirpf:17650000, dcbe:null, comments:""},
    ]},
    {name:"Créditos e Direitos", jurisdiction:"Brasil", items:[
      {id:7, desc:"Créditos a receber", loc:"Brasil", dirpf:2350000, dcbe:null, comments:""},
    ]},
    {name:"Contas Bancárias", jurisdiction:"Brasil", items:[
      {id:8, desc:"Conta Corrente / Poupança", loc:"Brasil", dirpf:612400, dcbe:null, comments:""},
    ]},
    {name:"Participações no Capital de Empresas no Exterior", jurisdiction:"Offshore", items:[
      {id:9, desc:"DOE FAMILY HOLDINGS LTD. (100%)", loc:"Ilhas Cayman", dirpf:null, dcbe:3420000, comments:""},
      {id:10, desc:"JD INVESTMENTS LLC (70%)", loc:"Delaware, EUA", dirpf:null, dcbe:1580000, comments:""},
    ]},
    {name:"Depósitos em Contas Bancárias no Exterior", jurisdiction:"Offshore", items:[
      {id:11, desc:"Citibank Private Bank", loc:"EUA", dirpf:null, dcbe:584300, comments:""},
      {id:12, desc:"Banco Santander Internacional", loc:"EUA", dirpf:null, dcbe:218700, comments:""},
      {id:13, desc:"HSBC Jersey", loc:"Ilha de Jersey", dirpf:null, dcbe:142500, comments:""},
    ]},
  ],
  debts:[
    {id:1, desc:"Financiamento imobiliário — Banco Itaú Unibanco S.A.", value:1620000},
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

function Toggle({on, onChange}){
  return (
    <div onClick={e=>{e.stopPropagation();onChange(!on);}}
      title={on?"Revisado ✓":"Marcar como revisado"}
      style={{
        width:36, height:20, borderRadius:10, cursor:"pointer",
        background: on ? "#4CAF50" : "#D0D0CE",
        position:"relative", transition:"background .2s", flexShrink:0,
        boxShadow: on ? "0 0 0 1px rgba(76,175,80,.4)" : "0 0 0 1px #C0C0BE",
      }}>
      <div style={{
        position:"absolute", top:2, left: on ? 18 : 2,
        width:16, height:16, borderRadius:"50%",
        background:"#fff", transition:"left .18s",
        boxShadow:"0 1px 3px rgba(0,0,0,.25)",
      }}/>
    </div>
  );
}

function GroupTable({group, onUpdate, onAddItem, dragSource, setDragSource, onMoveItem}){
  const [open,setOpen]=useState(true);
  const [openComment,setOpenComment]=useState({});
  const [isDragOver, setIsDragOver] = useState(false);

  // This group is a valid drop target when:
  // - something is being dragged
  // - from a DIFFERENT group, same jurisdiction
  const isValidDropTarget = dragSource
    && dragSource.juris === group.jurisdiction
    && dragSource.grpName !== group.name;

  const totD=group.items.reduce((a,i)=>a+(i.dirpf||0),0);
  const totC=group.items.reduce((a,i)=>a+(i.dcbe||0),0);
  const nReviewed = group.items.filter(i => i.reviewed).length;
  const toggleComment = (idx,e) => { e.stopPropagation(); setOpenComment(p=>({...p,[idx]:!p[idx]})); };
  // Pre-open the comment row if the item already has a saved comment
  useEffect(()=>{
    const init = {};
    group.items.forEach((item, idx) => { if (item.comments) init[idx] = true; });
    setOpenComment(prev => ({...init, ...prev}));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [group.name]);
  return(
    <div
      onDragOver={e => {
        if (isValidDropTarget) { e.preventDefault(); setIsDragOver(true); }
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={e => {
        if (isValidDropTarget) {
          e.preventDefault();
          onMoveItem(dragSource, group.name, group.jurisdiction);
          setIsDragOver(false);
        }
      }}
      style={{
        background: isDragOver && isValidDropTarget ? "rgba(76,175,80,.08)" : C.card,
        border: isValidDropTarget
          ? `2px dashed ${isDragOver ? "#4CAF50" : "#B8D8C2"}`
          : `1px solid ${C.border}`,
        borderRadius:10,
        marginBottom:10,
        overflow:"hidden",
        transition:"background .15s, border-color .15s",
      }}>
      <div onClick={()=>setOpen(!open)} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"14px 18px",cursor:"pointer",userSelect:"none"}}>
        <div style={{display:"flex",alignItems:"center",gap:10}}>
          <span style={{fontWeight:700,fontSize:13,color:C.text}}>{group.name}</span>
          <span style={{background:C.surface,color:C.muted,fontSize:10,padding:"2px 8px",borderRadius:20}}>{group.items.length} {group.items.length===1?"item":"itens"}</span>
          {nReviewed > 0 && (
            <span style={{background:"rgba(76,175,80,.12)",color:"#4CAF50",fontSize:10,fontWeight:700,padding:"2px 8px",borderRadius:20}}>
              ✓ {nReviewed}/{group.items.length}
            </span>
          )}
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
            <span style={{fontSize:10,color:C.dim}}>✏️ Clique em qualquer valor para editar · ⋮⋮ Arraste para mover entre categorias</span>
          </div>
          <table style={{width:"100%",borderCollapse:"collapse",fontSize:12,tableLayout:"auto"}}>
            <thead>
              <tr style={{background:C.surface}}>
                {[
                  {h:"#", w:36, align:"center"},
                  {h:"Descrição", w:"auto", align:"left"},
                  {h:"País / Local", w:160, align:"left"},
                  {h:"DIRPF (R$)", w:140, align:"right"},
                  {h:"DCBE (US$)", w:130, align:"right"},
                  {h:"", w:42, align:"right"},     // comment col — fixed
                  {h:"", w:56, align:"right"},     // toggle col — fixed
                ].map(({h,w,align},i)=>(
                  <th key={i} style={{padding:"7px 12px",color:C.muted,fontWeight:600,fontSize:10,letterSpacing:"0.08em",textTransform:"uppercase",textAlign:align,whiteSpace:"nowrap",width:typeof w==="number"?w+"px":w}}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {group.items.map((item,idx)=>[
                <tr key={(item.id||idx)+"r"} className="rh"
                  draggable
                  onDragStart={e => {
                    e.dataTransfer.effectAllowed = "move";
                    setDragSource({grpName: group.name, juris: group.jurisdiction, idx});
                  }}
                  onDragEnd={() => setDragSource(null)}
                  style={{
                    borderTop:`1px solid ${C.border}`,
                    cursor: "grab",
                    opacity: dragSource?.grpName===group.name && dragSource?.idx===idx ? 0.35 : 1,
                  }}>
                  <td style={{padding:"9px 4px 9px 12px",color:C.muted,textAlign:"center",fontSize:10,whiteSpace:"nowrap"}}>
                    <span style={{color:C.dim,marginRight:4,letterSpacing:"-2px",fontSize:11,userSelect:"none"}} title="Arraste para mover de categoria">⋮⋮</span>
                    {item.id}
                  </td>
                  <td style={{padding:"9px 12px",color:C.text,maxWidth:340}}>
                    {item.desc===''
                      ? <input defaultValue="" placeholder="Descrição do ativo" onBlur={e=>onUpdate(group.name,group.jurisdiction,idx,"desc",e.target.value)}
                          style={{background:"transparent",border:`1px solid ${C.border}`,borderRadius:4,padding:"3px 7px",color:C.text,fontSize:11,fontFamily:"'Nunito Sans',sans-serif",width:"100%"}}/>
                      : item.desc}
                  </td>
                  <td style={{padding:"9px 12px",color:C.muted,whiteSpace:"nowrap"}}>
                    {item.desc===''
                      ? <input defaultValue="" placeholder="País / Local" onBlur={e=>onUpdate(group.name,group.jurisdiction,idx,"loc",e.target.value)}
                          style={{background:"transparent",border:`1px solid ${C.border}`,borderRadius:4,padding:"3px 7px",color:C.muted,fontSize:11,fontFamily:"'Nunito Sans',sans-serif",width:90}}/>
                      : item.loc}
                  </td>
                  <td style={{padding:"9px 12px",textAlign:"right",fontFamily:"monospace",fontSize:11,color:C.text}}>
                    <EditCell value={item.dirpf} onChange={v=>onUpdate(group.name,group.jurisdiction,idx,"dirpf",v)}/>
                  </td>
                  <td style={{padding:"9px 12px",textAlign:"right",fontFamily:"monospace",fontSize:11,color:item.dcbe>0?C.goldBright:C.dim}}>
                    <EditCell value={item.dcbe>0?item.dcbe:null} onChange={v=>onUpdate(group.name,group.jurisdiction,idx,"dcbe",v)}/>
                  </td>
                  <td style={{padding:"9px 6px 9px 8px",textAlign:"center",width:42}}>
                    <button onClick={e=>toggleComment(idx,e)} title={item.comments?"Ver comentário":"Adicionar comentário"}
                      style={{background:"transparent",border:"none",cursor:"pointer",fontSize:13,padding:"2px 4px",
                        color: item.comments ? C.gold : C.muted,
                        opacity: openComment[idx] ? 1 : 0.6,
                      }}>
                      {item.comments ? "💬" : "🗒️"}
                    </button>
                  </td>
                  <td style={{padding:"9px 14px 9px 6px",textAlign:"right",width:56}}>
                    <Toggle on={!!item.reviewed} onChange={v=>onUpdate(group.name,group.jurisdiction,idx,"reviewed",v)}/>
                  </td>
                </tr>,
                openComment[idx] ? (
                  <tr key={(item.id||idx)+"c"} style={{background:C.surface}}>
                    <td colSpan={7} style={{padding:"8px 18px 10px"}}>
                      <div style={{display:"flex",alignItems:"flex-start",gap:8}}>
                        <span style={{fontSize:10,color:C.muted,paddingTop:6,whiteSpace:"nowrap"}}>Comentário</span>
                        <textarea
                          defaultValue={item.comments||""}
                          placeholder="Add Comments"
                          rows={2}
                          onBlur={e=>onUpdate(group.name,group.jurisdiction,idx,"comments",e.target.value)}
                          style={{flex:1,background:C.card,border:`1px solid ${C.border}`,borderRadius:6,padding:"7px 10px",color:C.text,fontSize:11,fontFamily:"'Nunito Sans',sans-serif",resize:"vertical",lineHeight:1.5}}
                        />
                      </div>
                    </td>
                  </tr>
                ) : null
              ])}
            </tbody>
            <tfoot>
              <tr style={{background:C.surface,borderTop:`1px solid ${C.borderLight}`}}>
                <td colSpan={3} style={{padding:"9px 12px",color:C.muted,fontSize:10,fontWeight:700,letterSpacing:"0.1em"}}>SUBTOTAL</td>
                <td style={{padding:"9px 12px",color:C.goldBright,textAlign:"right",fontFamily:"monospace",fontWeight:700,fontSize:12}}>{n(totD)}</td>
                <td style={{padding:"9px 12px",color:C.goldBright,textAlign:"right",fontFamily:"monospace",fontWeight:700,fontSize:11}}>{totC>0?n(totC):"—"}</td>
                <td/><td/>
              </tr>
            </tfoot>
          </table>
          {/* + Adicionar item row */}
          {onAddItem && (
            <div style={{padding:"8px 18px",borderTop:`1px dashed ${C.border}`}}>
              <button onClick={()=>onAddItem(group.name,group.jurisdiction)}
                style={{background:"transparent",color:C.muted,border:"none",cursor:"pointer",fontFamily:"'Nunito Sans',sans-serif",fontSize:11,fontWeight:600,display:"flex",alignItems:"center",gap:5,padding:0}}>
                <span style={{fontSize:15,lineHeight:1}}>+</span> Adicionar item
              </button>
            </div>
          )}
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
      // Hydrate items with previously-saved review state and comments
      if (parsed?.groups && parsed?.client) {
        parsed.groups = hydrateItemsFromStore(parsed.groups, parsed.client);
      }
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

  // Lightweight toast for "saved" feedback
  const [savedToast, setSavedToast] = useState(false);
  const showSavedToast = () => {
    setSavedToast(true);
    setTimeout(()=>setSavedToast(false), 1400);
  };

  const updateItem = (grpName, juris, idx, field, value) => {
    // Persist to localStorage FIRST (synchronous side effect, outside reducer)
    if ((field === "comments" || field === "reviewed") && data?.client) {
      try {
        const grp = data.groups.find(g => g.name === grpName && g.jurisdiction === juris);
        const item = grp?.items?.[idx];
        if (item?.desc) {
          const k = normalizeKey(item.desc);
          if (k) {
            const store = loadReviewStore(data.client);
            const cur = store[k] || {};
            store[k] = {
              ...cur,
              ...(field === "comments" ? {comments: value} : {}),
              ...(field === "reviewed" ? {reviewed: value} : {}),
            };
            if (!store[k].comments && !store[k].reviewed) delete store[k];
            saveReviewStore(data.client, store);
            showSavedToast();
          }
        }
      } catch(e) { console.error("Save error:", e); }
    }
    // Then update React state
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

  const addItemToGroup = (grpName, juris) => {
    setData(prev => {
      const groups = prev.groups.map(g => {
        if (g.name === grpName && g.jurisdiction === juris) {
          const newId = (g.items.reduce((a,i)=>Math.max(a,i.id||0),0))+1;
          return {...g, items:[...g.items, {id:newId, desc:"", loc:"", dirpf:null, dcbe:null, comments:""}]};
        }
        return g;
      });
      return {...prev, groups};
    });
  };

  // ── Drag & drop: move items between groups within the same jurisdiction ──
  const [dragSource, setDragSource] = useState(null);  // {grpName, juris, idx}
  const moveItem = (src, destGrpName, destJuris) => {
    if (src.grpName === destGrpName && src.juris === destJuris) return;
    if (src.juris !== destJuris) return;  // same currency/jurisdiction only
    setData(prev => {
      let moved = null;
      const cleaned = prev.groups.map(g => {
        if (g.name === src.grpName && g.jurisdiction === src.juris) {
          moved = g.items[src.idx];
          return {...g, items: g.items.filter((_, i) => i !== src.idx)};
        }
        return g;
      });
      if (!moved) return prev;
      const withAdded = cleaned.map(g => {
        if (g.name === destGrpName && g.jurisdiction === destJuris) {
          return {...g, items: [...g.items, moved]};
        }
        return g;
      });
      return {...prev, groups: withAdded};
    });
    setDragSource(null);
  };

  const addOutrosGroup = (juris) => {
    const name = juris === "Brasil" ? "Outros Ativos" : "Outros Ativos no Exterior";
    setData(prev => {
      const exists = prev.groups.some(g => g.name === name && g.jurisdiction === juris);
      if (exists) {
        // Group already exists — just add a new blank item to it
        addItemToGroup(name, juris);
        setActiveCat(name);
        return prev;
      }
      const newGrp = {name, jurisdiction: juris, items:[{id:1, desc:"", loc:"", dirpf:null, dcbe:null, comments:""}]};
      return {...prev, groups:[...prev.groups, newGrp]};
    });
    setActiveJuris(juris);
    setTimeout(()=>setActiveCat(juris==="Brasil"?"Outros Ativos":"Outros Ativos no Exterior"),50);
  };

  const updateDebt = (idx, field, value) => {
    setData(prev => {
      const debts = (prev.debts||[]).map((d,i)=>i===idx?{...d,[field]:value}:d);
      return {...prev, debts};
    });
  };

  const addDebt = () => {
    setData(prev => {
      const id = ((prev.debts||[]).reduce((a,d)=>Math.max(a,d.id||0),0))+1;
      return {...prev, debts:[...(prev.debts||[]), {id, desc:"", value:null}]};
    });
  };

  const totDIRPF=data?.groups?.reduce((a,g)=>a+g.items.reduce((b,i)=>b+(i.dirpf||0),0),0)||0;
  const totDCBE=data?.groups?.reduce((a,g)=>a+g.items.reduce((b,i)=>b+(i.dcbe||0),0),0)||0;
  const nItems=data?.groups?.reduce((a,g)=>a+g.items.length,0)||0;
  const brGrps=data?.groups?.filter(g=>g.jurisdiction==="Brasil")||[];
  const offGrps=data?.groups?.filter(g=>g.jurisdiction==="Offshore")||[];

  // Tab state for verify-screen filtering. Default to "Brasil" if it has
  // groups, otherwise "Offshore". "Todos" picked for each category to show
  // all assets in that jurisdiction.
  const [activeJuris, setActiveJuris] = useState("Brasil");
  const [activeCat, setActiveCat] = useState("Todos");

  // PTAX state — exchange rate USD→BRL fetched from Banco Central (BCB).
  // Default date is 31/12/yyyy of the AC (calendar year) of the documents.
  const defaultPtaxDate = data?.year ? `31/12/${data.year}` : "31/12/2024";
  const [ptaxDate, setPtaxDate] = useState(defaultPtaxDate);
  const [ptaxRate, setPtaxRate] = useState(null);
  const [ptaxLoading, setPtaxLoading] = useState(false);
  const [ptaxError, setPtaxError] = useState("");

  const fetchPtax = async () => {
    setPtaxLoading(true); setPtaxError(""); setPtaxRate(null);
    // Parse dd/mm/yyyy → mm-dd-yyyy as required by BCB API
    const m = ptaxDate.trim().match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (!m) { setPtaxError("Use o formato dd/mm/aaaa"); setPtaxLoading(false); return; }
    const [, dd, mm, yyyy] = m;
    const apiDate = `${mm}-${dd}-${yyyy}`;
    // BCB Olinda dataset: PTAX USD venda. We try the requested date, then walk
    // back up to 7 days if the market was closed that day (weekend/holiday).
    let triedDates = [];
    for (let i = 0; i < 8; i++) {
      const d = new Date(parseInt(yyyy), parseInt(mm)-1, parseInt(dd) - i);
      const formatted = `${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}-${d.getFullYear()}`;
      triedDates.push(formatted);
      const url = `https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao=%27${formatted}%27&%24format=json&%24select=cotacaoVenda,dataHoraCotacao`;
      try {
        const r = await fetch(url);
        if (r.ok) {
          const j = await r.json();
          if (j?.value?.length > 0) {
            setPtaxRate(j.value[0].cotacaoVenda);
            setPtaxLoading(false);
            return;
          }
        }
      } catch (e) { /* try next date */ }
    }
    setPtaxError(`Cotação não encontrada para ${ptaxDate} (mercado fechado?). Tentou ${triedDates.length} dias.`);
    setPtaxLoading(false);
  };

  // Reset category when jurisdiction changes so we don't end up showing
  // a category that doesn't exist in the new jurisdiction.
  useEffect(()=>{ setActiveCat("Todos"); }, [activeJuris]);
  // When data first loads, prefer the jurisdiction that actually has groups.
  useEffect(()=>{
    if (!data) return;
    if (brGrps.length === 0 && offGrps.length > 0) setActiveJuris("Offshore");
    else setActiveJuris("Brasil");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const activeGrps = activeJuris === "Brasil" ? brGrps : offGrps;
  // While dragging, show ALL groups so the user can drop on any target
  const visibleGrps = dragSource
    ? activeGrps
    : (activeCat === "Todos"
        ? activeGrps
        : activeGrps.filter(g => g.name === activeCat));

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
          <button className="gh" style={{background:"transparent",color:C.muted,padding:"13px 22px",borderRadius:8,border:`1px solid ${C.border}`,cursor:"pointer",fontFamily:"'Nunito Sans',sans-serif",fontSize:13}} onClick={()=>{setData({...DEMO, groups: hydrateItemsFromStore(DEMO.groups, DEMO.client)});setStep("verify");}}>Usar Dados Demo</button>
        </div>
        <p style={{textAlign:"center",color:C.dim,fontSize:11,lineHeight:1.6}}>Os documentos são processados via API e não são armazenados.<br/>Também é possível carregar apenas um dos dois arquivos.</p>
      </div>
    </div>
  );

  if(step==="verify")return(
    <div style={{background:C.bg,minHeight:"100vh",fontFamily:"'Nunito Sans',sans-serif",color:C.text,padding:"24px 20px"}} className="fi">
      <style>{style}</style>
      {/* Saved toast */}
      {savedToast && (
        <div style={{
          position:"fixed", bottom:24, right:24, zIndex:9999,
          background:"#4CAF50", color:"#fff",
          padding:"10px 18px", borderRadius:8,
          fontFamily:"'Nunito Sans',sans-serif", fontSize:12, fontWeight:700,
          letterSpacing:"0.05em", boxShadow:"0 6px 24px rgba(76,175,80,.4)",
        }}>✓ Salvo</div>
      )}
      <div style={{maxWidth:980,margin:"0 auto"}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:24,flexWrap:"wrap",gap:12}}>
          <div>
            <p style={{color:C.muted,fontSize:10,fontWeight:700,letterSpacing:"0.2em",marginBottom:4}}>VERIFICAÇÃO DOS DADOS · CONFIDENCIAL</p>
            <h1 style={{fontFamily:"'Cormorant Garamond',serif",fontSize:28,fontWeight:600,color:C.text}}>{data?.client||"—"}</h1>
            <p style={{color:C.muted,fontSize:12,marginTop:2}}>Ano-calendário {data?.year} · {data?.groups?.length} categorias · {nItems} itens · <span style={{color:C.dim,fontSize:11}}>⚿ dados anonimizados</span></p>
          </div>
          <div style={{display:"flex",gap:10,alignItems:"center"}}>
            <button className="gh"
              title="Apaga revisões e comentários salvos deste cliente neste navegador"
              style={{background:"transparent",color:C.muted,padding:"10px 14px",borderRadius:8,border:`1px solid ${C.border}`,cursor:"pointer",fontFamily:"'Nunito Sans',sans-serif",fontSize:11}}
              onClick={()=>{
                if (!data?.client) return;
                if (confirm(`Apagar todas as revisões e comentários salvos de ${data.client}?\n\nIsto remove os dados deste navegador (não afeta outros usuários).`)) {
                  try { localStorage.removeItem(reviewStoreKey(data.client)); } catch(e) {}
                  setData(prev => ({
                    ...prev,
                    groups: prev.groups.map(g => ({
                      ...g,
                      items: g.items.map(it => ({...it, reviewed: false, comments: ""})),
                    })),
                  }));
                }
              }}>
              🧹 Limpar revisão
            </button>
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

        {/* PTAX row — only when client has offshore assets */}
        {offGrps.length > 0 && (() => {
          const totOff = offGrps.reduce((a,g)=>a+g.items.reduce((b,i)=>b+(i.dcbe||0),0),0);
          const offBrl = ptaxRate ? totOff * ptaxRate : null;
          return (
            <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:10,padding:"14px 16px",marginBottom:16,display:"grid",gridTemplateColumns:"auto auto auto 1fr",gap:14,alignItems:"center"}}>
              <div>
                <p style={{color:C.muted,fontSize:9,fontWeight:700,letterSpacing:"0.15em",marginBottom:4}}>PTAX BCB (USD/BRL)</p>
                <p style={{fontFamily:"'Cormorant Garamond',serif",fontSize:22,fontWeight:600,color:ptaxRate?C.gold:C.muted}}>
                  {ptaxRate ? `R$ ${ptaxRate.toFixed(4)}` : "—"}
                </p>
              </div>
              <input
                value={ptaxDate}
                onChange={e=>setPtaxDate(e.target.value)}
                placeholder="dd/mm/aaaa"
                style={{background:C.bg,border:`1px solid ${C.border}`,borderRadius:6,padding:"8px 10px",color:C.text,fontSize:12,fontFamily:"'Nunito Sans',sans-serif",width:110}}
              />
              <button onClick={fetchPtax} disabled={ptaxLoading}
                style={{background:"transparent",color:C.gold,border:`1px solid ${C.gold}`,borderRadius:6,padding:"8px 14px",cursor:ptaxLoading?"wait":"pointer",fontFamily:"'Nunito Sans',sans-serif",fontSize:11,fontWeight:700,letterSpacing:"0.05em"}}>
                {ptaxLoading ? "Buscando..." : "Buscar PTAX"}
              </button>
              {ptaxError ? (
                <p style={{color:C.red,fontSize:11,textAlign:"right"}}>⚠ {ptaxError}</p>
              ) : offBrl !== null ? (
                <div style={{textAlign:"right"}}>
                  <p style={{color:C.muted,fontSize:9,fontWeight:700,letterSpacing:"0.15em",marginBottom:4}}>OFFSHORE EM BRL</p>
                  <p style={{fontFamily:"'Cormorant Garamond',serif",fontSize:22,fontWeight:600,color:C.gold}}>{brl(offBrl)}</p>
                </div>
              ) : (
                <p style={{color:C.muted,fontSize:11,textAlign:"right",fontStyle:"italic"}}>Busque a cotação para converter o total offshore em R$</p>
              )}
            </div>
          );
        })()}

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
        {/* Jurisdiction tabs (Brasil / Offshore) */}
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:14}}>
          {[
            {
              key:"Brasil", label:"🇧🇷 Brasil", accent:C.green,
              total: brl(brGrps.reduce((a,g)=>a+g.items.reduce((b,i)=>b+(i.dirpf||0),0),0)),
              n: brGrps.length,
              items: brGrps.reduce((a,g)=>a+g.items.length,0),
              // Count unique states/cities from item.loc
              locs: (()=>{
                const counts={};
                brGrps.forEach(g=>g.items.forEach(i=>{
                  if(i.loc){const k=i.loc.toString().trim(); counts[k]=(counts[k]||0)+1;}
                }));
                return counts;
              })(),
            },
            {
              key:"Offshore", label:"🌐 Offshore", accent:C.gold,
              total: (()=>{const t=offGrps.reduce((a,g)=>a+g.items.reduce((b,i)=>b+(i.dcbe||0),0),0); return t>0?usd(t):"N/A";})(),
              n: offGrps.length,
              items: offGrps.reduce((a,g)=>a+g.items.length,0),
              // Count unique countries from item.loc
              locs: (()=>{
                const counts={};
                offGrps.forEach(g=>g.items.forEach(i=>{
                  if(i.loc){const k=i.loc.toString().trim(); counts[k]=(counts[k]||0)+1;}
                }));
                return counts;
              })(),
            },
          ].map(({key,label,accent,total,n,items,locs}) => {
            const isActive = activeJuris === key;
            const disabled = n === 0;
            const locEntries = Object.entries(locs).sort((a,b)=>b[1]-a[1]);
            return (
              <button key={key}
                disabled={disabled}
                onClick={()=>!disabled && setActiveJuris(key)}
                style={{
                  background: isActive ? (key==="Brasil" ? "rgba(60,174,122,.06)" : "rgba(191,148,71,.06)") : C.card,
                  border: `1.5px solid ${isActive ? accent : C.border}`,
                  borderRadius: 10,
                  padding: "14px 18px",
                  cursor: disabled ? "not-allowed" : "pointer",
                  textAlign: "left",
                  fontFamily: "'Nunito Sans',sans-serif",
                  opacity: disabled ? 0.4 : 1,
                  width: "100%",
                }}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom: locEntries.length>0 ? 10 : 0}}>
                  <div>
                    <p style={{color:isActive?accent:C.text,fontSize:14,fontWeight:700,marginBottom:3}}>{label}</p>
                    <p style={{color:C.muted,fontSize:10}}>{n} categorias · {items} {items===1?"item":"itens"}</p>
                  </div>
                  <p style={{color:isActive?accent:C.text,fontSize:14,fontFamily:"'Cormorant Garamond',serif",fontWeight:600,whiteSpace:"nowrap",marginLeft:12}}>{total}</p>
                </div>
                {/* Country/location breakdown pills */}
                {locEntries.length > 0 && (
                  <div style={{display:"flex",flexWrap:"wrap",gap:5}}>
                    {locEntries.map(([loc,cnt])=>(
                      <span key={loc} style={{
                        background: isActive ? (key==="Brasil"?"rgba(60,174,122,.12)":"rgba(191,148,71,.12)") : "rgba(142,149,155,.1)",
                        color: isActive ? accent : C.muted,
                        border: `1px solid ${isActive ? accent+"44" : C.border}`,
                        borderRadius: 999,
                        padding: "3px 9px",
                        fontSize: 10,
                        fontWeight: 600,
                        whiteSpace: "nowrap",
                      }}>
                        {loc}{cnt>1?` · ${cnt}`:""}
                      </span>
                    ))}
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Category sub-tabs + add Outros button */}
        {activeGrps.length > 0 && (
          <div style={{display:"flex",flexWrap:"wrap",gap:8,marginBottom:14,alignItems:"center"}}>
            {["Todos", ...activeGrps.map(g=>g.name)].map(catName => {
              const isActive = activeCat === catName;
              const count = catName === "Todos"
                ? activeGrps.reduce((a,g)=>a+g.items.length,0)
                : (activeGrps.find(g=>g.name===catName)?.items.length || 0);
              return (
                <button key={catName}
                  onClick={()=>setActiveCat(catName)}
                  style={{
                    background: isActive ? C.text : C.card,
                    color: isActive ? C.bg : C.text,
                    border: `1px solid ${isActive ? C.text : C.border}`,
                    borderRadius: 999,
                    padding: "7px 14px",
                    cursor: "pointer",
                    fontFamily: "'Nunito Sans',sans-serif",
                    fontSize: 12,
                    fontWeight: isActive ? 700 : 500,
                  }}>
                  {catName} <span style={{opacity:0.55,marginLeft:4,fontSize:10}}>{count}</span>
                </button>
              );
            })}
            {/* + Outros button */}
            <button
              onClick={()=>addOutrosGroup(activeJuris)}
              style={{
                background:"transparent",
                color:C.muted,
                border:`1px dashed ${C.border}`,
                borderRadius:999,
                padding:"7px 14px",
                cursor:"pointer",
                fontFamily:"'Nunito Sans',sans-serif",
                fontSize:12,
                fontWeight:500,
                display:"flex",alignItems:"center",gap:5,
              }}>
              <span style={{fontSize:14,lineHeight:1}}>+</span> Outros
            </button>
          </div>
        )}

        {/* Filtered groups */}
        {visibleGrps.length === 0 ? (
          <div style={{background:C.card,border:`1px dashed ${C.border}`,borderRadius:10,padding:"40px 20px",textAlign:"center",color:C.muted,fontSize:13,marginBottom:20}}>
            Nenhum ativo em {activeJuris}{activeCat !== "Todos" ? ` · ${activeCat}` : ""}.
          </div>
        ) : (
          <div style={{marginBottom:20}}>
            {visibleGrps.map(g=><GroupTable key={g.name+g.jurisdiction} group={g} onUpdate={updateItem} onAddItem={addItemToGroup} dragSource={dragSource} setDragSource={setDragSource} onMoveItem={moveItem}/>)}
          </div>
        )}

        {/* ── Dívidas e Ônus Reais ──────────────────────────────────────── */}
        {(() => {
          const debts = data?.debts || [];
          const totDebts = debts.reduce((a,d)=>a+(d.value||0),0);
          const netWorth = totDIRPF - totDebts;
          return (
            <div style={{marginTop:8,marginBottom:16}}>
              {/* Header */}
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:8}}>
                <div style={{display:"flex",alignItems:"center",gap:8}}>
                  <div style={{width:3,height:14,background:C.red,borderRadius:2}}/>
                  <span style={{color:C.red,fontWeight:700,fontSize:11,letterSpacing:"0.15em"}}>DÍVIDAS E ÔNUS REAIS</span>
                  <span style={{color:C.muted,fontSize:10}}>(Ficha 8 DIRPF)</span>
                </div>
                {totDebts>0&&<span style={{color:C.red,fontFamily:"'Cormorant Garamond',serif",fontSize:15,fontWeight:600}}>− {brl(totDebts)}</span>}
              </div>

              {debts.length === 0 ? (
                <div style={{background:C.card,border:`1px dashed ${C.border}`,borderRadius:8,padding:"12px 16px",color:C.muted,fontSize:12,marginBottom:8}}>
                  Nenhuma dívida declarada.
                </div>
              ) : (
                <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:8,overflow:"hidden",marginBottom:8}}>
                  <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
                    <thead>
                      <tr style={{background:C.surface}}>
                        {["#","Descrição da Dívida / Credor","Valor (R$)",""].map((h,i)=>(
                          <th key={i} style={{padding:"7px 12px",color:C.muted,fontWeight:600,fontSize:10,letterSpacing:"0.08em",textTransform:"uppercase",textAlign:i>=2?"right":"left",whiteSpace:"nowrap"}}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {debts.map((d,idx)=>(
                        <tr key={d.id||idx} className="rh" style={{borderTop:`1px solid ${C.border}`}}>
                          <td style={{padding:"9px 12px",color:C.muted,fontSize:10,width:32}}>{d.id}</td>
                          <td style={{padding:"9px 12px",color:C.text}}>
                            {d.desc===''||d.desc==null
                              ? <input defaultValue="" placeholder="Ex: Financiamento Bradesco" onBlur={e=>updateDebt(idx,"desc",e.target.value)}
                                  style={{background:"transparent",border:`1px solid ${C.border}`,borderRadius:4,padding:"3px 7px",color:C.text,fontSize:11,fontFamily:"'Nunito Sans',sans-serif",width:"100%"}}/>
                              : d.desc}
                          </td>
                          <td style={{padding:"9px 12px",textAlign:"right",fontFamily:"monospace",fontSize:11,color:C.red}}>
                            <EditCell value={d.value} onChange={v=>updateDebt(idx,"value",v)}/>
                          </td>
                          <td style={{padding:"9px 8px",width:32}}/>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr style={{background:C.surface,borderTop:`1px solid ${C.borderLight}`}}>
                        <td colSpan={2} style={{padding:"9px 12px",color:C.muted,fontSize:10,fontWeight:700,letterSpacing:"0.1em"}}>TOTAL DÍVIDAS</td>
                        <td style={{padding:"9px 12px",color:C.red,textAlign:"right",fontFamily:"monospace",fontWeight:700,fontSize:12}}>{totDebts>0?`− ${n(totDebts)}`:"—"}</td>
                        <td/>
                      </tr>
                    </tfoot>
                  </table>
                  <div style={{padding:"8px 18px",borderTop:`1px dashed ${C.border}`}}>
                    <button onClick={addDebt}
                      style={{background:"transparent",color:C.muted,border:"none",cursor:"pointer",fontFamily:"'Nunito Sans',sans-serif",fontSize:11,fontWeight:600,display:"flex",alignItems:"center",gap:5,padding:0}}>
                      <span style={{fontSize:15,lineHeight:1}}>+</span> Adicionar dívida
                    </button>
                  </div>
                </div>
              )}

              {/* Net Worth card */}
              <div style={{
                background: totDebts>0 ? "rgba(32,60,92,.06)" : C.card,
                border: `1.5px solid ${totDebts>0 ? C.blue : C.borderLight}`,
                borderRadius:10, padding:"16px 20px",
                display:"flex", justifyContent:"space-between", alignItems:"center",
              }}>
                <div>
                  <p style={{color:C.muted,fontSize:10,fontWeight:700,letterSpacing:"0.15em",marginBottom:4}}>PATRIMÔNIO LÍQUIDO</p>
                  <p style={{color:C.dim,fontSize:10}}>Total ativos{totDebts>0?" − dívidas":""}</p>
                </div>
                <div style={{textAlign:"right"}}>
                  <p style={{color:C.text,fontSize:24,fontFamily:"'Cormorant Garamond',serif",fontWeight:700}}>{brl(netWorth)}</p>
                  {totDCBE>0&&<p style={{color:C.gold,fontSize:12,marginTop:2}}>{usd(totDCBE)} offshore</p>}
                </div>
              </div>
            </div>
          );
        })()}

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
