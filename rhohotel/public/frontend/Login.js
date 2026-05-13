import{c as l,r as i,u as M,a as C,b as S,o as a,d as g,e as t,f as z,g as y,h as s,i as p,t as f,w as h,v as I,n as k,j as L,k as V,l as v}from"./index.js";/**
 * @license lucide-vue-next v0.378.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const j=l("CircleCheckBigIcon",[["path",{d:"M22 11.08V12a10 10 0 1 1-5.93-9.14",key:"g774vq"}],["path",{d:"m9 11 3 3L22 4",key:"1pflzl"}]]);/**
 * @license lucide-vue-next v0.378.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const R=l("CircleXIcon",[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["path",{d:"m15 9-6 6",key:"1uzhvr"}],["path",{d:"m9 9 6 6",key:"z0biqf"}]]);/**
 * @license lucide-vue-next v0.378.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const E=l("EyeOffIcon",[["path",{d:"M9.88 9.88a3 3 0 1 0 4.24 4.24",key:"1jxqfv"}],["path",{d:"M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68",key:"9wicm4"}],["path",{d:"M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61",key:"1jreej"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22",key:"a6p6uj"}]]);/**
 * @license lucide-vue-next v0.378.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const B=l("EyeIcon",[["path",{d:"M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z",key:"rwhkz3"}],["circle",{cx:"12",cy:"12",r:"3",key:"1v7zrd"}]]);/**
 * @license lucide-vue-next v0.378.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const D=l("LoaderCircleIcon",[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56",key:"13zald"}]]);/**
 * @license lucide-vue-next v0.378.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const N=l("LockIcon",[["rect",{width:"18",height:"11",x:"3",y:"11",rx:"2",ry:"2",key:"1w4ew1"}],["path",{d:"M7 11V7a5 5 0 0 1 10 0v4",key:"fwvmzm"}]]);/**
 * @license lucide-vue-next v0.378.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const q=l("MailIcon",[["rect",{width:"20",height:"16",x:"2",y:"4",rx:"2",key:"18n3k1"}],["path",{d:"m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7",key:"1ocrg3"}]]),P={class:"min-h-screen flex items-center justify-center",style:{"background-color":"#f1f5f9"}},A={class:"w-full max-w-md px-4"},H={class:"bg-white rounded-2xl shadow-2xl overflow-hidden"},K={class:"p-8"},O={key:0,class:"mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2"},T={key:1,class:"mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2"},U={class:"text-red-700 text-sm font-medium"},X={class:"space-y-4"},F={class:"relative"},W={class:"relative"},Y=["type"],Z=["disabled"],$={class:"text-center text-xs text-gray-400 mt-6"},Q={__name:"Login",setup(G){const r=i(""),n=i(""),o=i(""),d=i(!1),c=i(!1),w=M(),_=C(),u=S({url:"login",async onSuccess(){d.value=!0,o.value="",await _.initialize(!0),setTimeout(()=>{w.push({name:"RoomView"})},800)},onError(b){var e;o.value=((e=b.messages)==null?void 0:e[0])||"Invalid email or password. Please try again.",d.value=!1}});function x(){!r.value||!n.value||(o.value="",d.value=!1,u.submit({usr:r.value,pwd:n.value}))}return(b,e)=>(a(),g("div",P,[t("div",A,[t("div",H,[e[7]||(e[7]=t("div",{class:"h-1 w-full bg-gradient-to-r from-blue-500 via-blue-600 to-indigo-600"},null,-1)),t("div",K,[e[6]||(e[6]=z('<div class="mb-8"><div class="flex items-center gap-2 mb-3"><div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center"><span class="text-white font-bold text-sm">R</span></div><span class="text-gray-900 font-bold text-xl">Rho-HMS</span></div><h1 class="text-2xl font-bold text-gray-900">Welcome back</h1><p class="text-gray-500 text-sm mt-1">Sign in to your hotel management account</p></div>',1)),d.value?(a(),g("div",O,[y(s(j),{class:"w-4 h-4 text-green-500 flex-shrink-0"}),e[3]||(e[3]=t("p",{class:"text-green-700 text-sm font-medium"},"Login successful! Redirecting...",-1))])):p("",!0),o.value?(a(),g("div",T,[y(s(R),{class:"w-4 h-4 text-red-500 flex-shrink-0"}),t("p",U,f(o.value),1)])):p("",!0),t("div",X,[t("div",null,[e[4]||(e[4]=t("label",{class:"block text-sm font-medium text-gray-700 mb-1.5"},"Email address",-1)),t("div",F,[y(s(q),{class:"absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"}),h(t("input",{"onUpdate:modelValue":e[0]||(e[0]=m=>r.value=m),type:"email",class:k(["w-full pl-10 pr-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors",{"border-red-300 focus:ring-red-500 focus:border-red-500":o.value}]),placeholder:"you@example.com"},null,2),[[I,r.value]])])]),t("div",null,[e[5]||(e[5]=t("label",{class:"block text-sm font-medium text-gray-700 mb-1.5"},"Password",-1)),t("div",W,[y(s(N),{class:"absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"}),h(t("input",{"onUpdate:modelValue":e[1]||(e[1]=m=>n.value=m),type:c.value?"text":"password",class:k(["w-full pl-10 pr-10 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors",{"border-red-300 focus:ring-red-500 focus:border-red-500":o.value}]),placeholder:"\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022",onKeyup:V(x,["enter"])},null,42,Y),[[L,n.value]]),t("button",{type:"button",onClick:e[2]||(e[2]=m=>c.value=!c.value),class:"absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"},[c.value?(a(),v(s(E),{key:1,class:"w-4 h-4"})):(a(),v(s(B),{key:0,class:"w-4 h-4"}))])])]),t("button",{onClick:x,disabled:s(u).loading||!r.value||!n.value,class:"w-full py-2.5 rounded-lg text-sm font-semibold text-white transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2",style:{"background-color":"#1a1f2e"}},[s(u).loading?(a(),v(s(D),{key:0,class:"w-4 h-4 animate-spin"})):p("",!0),t("span",null,f(s(u).loading?"Signing in...":"Sign in"),1)],8,Z)]),t("p",$," Rhocom Hotel Management System \xA9 "+f(new Date().getFullYear()),1)])])])]))}};export{Q as default};
