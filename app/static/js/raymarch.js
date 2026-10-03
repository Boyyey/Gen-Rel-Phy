/**
 * Original geodesic disk renderer + orbit camera.
 * Drag to orbit, wheel to zoom, right-drag to change inclination.
 * Dual compact objects are capture spheres + extra deflection — the
 * Einstein solver lives in Python; this is the booth's light.
 */
function createBlackHoleRenderer(canvas) {
  const gl = canvas.getContext("webgl", { antialias: false, alpha: false, preserveDrawingBuffer: true });
  if (!gl) throw new Error("WebGL required");

  function compile(src, type) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      throw new Error(gl.getShaderInfoLog(s) || "compile");
    }
    return s;
  }

  const vert = `attribute vec2 p; void main(){ gl_Position = vec4(p,0.0,1.0); }`;
  const frag = `
    precision highp float;
    uniform vec2  iResolution;
    uniform float iTime;
    uniform float uSpin, uGrid, uDisk, uSep, uPhase, uM1, uM2, uFieldM1, uFieldM2, uType1, uType2, uWave, uMerger, uSimMode, uCentralBH;
    uniform float uCamAz, uCamEl, uCamDist;

    float hash12(vec2 p){
      vec3 p3 = fract(vec3(p.xyx)*0.1031);
      p3 += dot(p3, p3.yzx+33.33);
      return fract((p3.x+p3.y)*p3.z);
    }
    float n2(vec2 p){
      vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
      return mix(mix(hash12(i),hash12(i+vec2(1,0)),f.x), mix(hash12(i+vec2(0,1)),hash12(i+vec2(1,1)),f.x), f.y);
    }
    float fbm(vec2 p){ float v=0.0,a=0.5; for(int i=0;i<5;i++){ v+=a*n2(p); p=p*2.15+vec2(7.1,3.4); a*=0.5;} return v; }

    vec3 bb(float T){
      T=clamp(T,0.5,14.0);
      vec3 c=vec3(1.0, clamp(0.3+0.09*T,0.,1.), clamp(0.03+0.01*T*T,0.,1.3));
      if(T<3.4){ c.g*=T/3.4; c.b*=T/5.0; }
      return c*(0.28+0.2*T);
    }
    vec3 sky(vec3 d){
      d=normalize(d);
      float lat=d.y, lon=atan(d.z,d.x);
      float band=exp(-pow(lat*3.3+0.18*sin(lon*2.8),2.0)*8.5);
      float dust=fbm(vec2(lon*2.0,lat*6.0)*2.0);
      vec3 lane=mix(vec3(0.28,0.4,0.9), vec3(1.0,0.76,0.5), dust);
      float st=step(0.988, hash12(d.xy*85.0+d.z*40.0));
      float gt=step(0.997, hash12(d.zx*55.0+4.2));
      return vec3(0.004,0.006,0.02)+lane*band*(0.2+0.55*dust)+st*vec3(0.85,0.9,1.0)*1.5+gt*vec3(1.0,0.7,0.4)*3.2;
    }

    vec3 diskAt(vec3 p, vec3 dir, vec3 c, float M, float chi, float t){
      vec3 q=p-c;
      float rho=length(q.xz);
      float isco=mix(6.0,2.25,clamp(chi,0.,1.))*M;
      float outer=32.0*M;
      if(rho<isco*0.85 || rho>outer) return vec3(0.0);
      float thick=0.48*M*(0.75+0.6*rho/(10.0*M));
      float vert=exp(-0.5*(q.y/thick)*(q.y/thick));
      if(vert<0.003) return vec3(0.0);
      float phi=atan(q.z,q.x);
      float y=log(max(rho/M,1.1));
      float spiral=phi-1.7*y-t*(0.55+0.9*chi);
      float turb=fbm(vec2(spiral*0.88,y*2.4)*1.5);
      float arms=0.35+0.65*pow(0.5+0.5*sin(2.0*spiral+turb*4.5),2.0);
      float rad=smoothstep(isco*0.85,isco*1.2,rho)*smoothstep(outer,outer*0.5,rho);
      vec3 ephi=vec3(-q.z,0.0,q.x)/max(rho,1e-4);
      float vk=sqrt(M/max(rho,isco))/(1.0+0.35*chi);
      float mu=clamp(dot(normalize(dir),ephi),-0.95,0.95);
      float dop=(1.0+0.25*chi)/max(0.1,1.0-vk*mu);
      float grav=sqrt(max(0.04,1.0-2.0*M/max(length(q),2.05*M)));
      float T=9.2*pow(isco/max(rho,isco),0.72);
      vec3 col=bb(T*mix(0.7,1.5,clamp(dop*0.5,0.,1.)));
      col=mix(col*vec3(1.25,0.35,0.12), col*vec3(0.68,0.95,1.45), smoothstep(0.68,1.45,dop));
      // Add accretion disk intensity variation
      float noise=fbm(vec2(phi*3.0, rho*0.15)*2.0);
      col*=0.85+0.3*noise;
      return col*vert*arms*rad*(0.5+0.75*turb)*pow(dop,3.2)*grav*2.3;
    }

    vec3 shadeBody(float typ, vec3 n){
      float lamb = 0.2 + 0.8*max(0.0, dot(n, normalize(vec3(0.4,0.85,0.2))));
      float rim = pow(1.0-max(0.0, n.y*0.3+0.5), 2.0);
      if(typ < 0.5) return vec3(0.0); // Black hole - no light
      if(typ < 1.5) return vec3(1.55,0.88,0.52)*lamb + vec3(0.4,0.7,1.0)*rim*0.25; // Neutron star
      if(typ < 2.5) return vec3(1.55,1.15,0.42)*(0.7+0.9*lamb); // Star
      if(typ < 3.5) return vec3(0.58,0.60,0.66)*lamb + vec3(0.15,0.18,0.22)*rim; // Mass sphere
      return mix(vec3(0.08,0.22,0.28),vec3(0.26,0.48,0.43),lamb)*0.9 + vec3(0.34,0.76,0.88)*rim*0.3; // Rocky planet
    }
    float radiusOf(float typ, float M){
      if(typ < 0.5) return 2.05*M; // Black hole
      if(typ < 1.5) return 3.35*M; // Neutron star
      if(typ < 2.5) return 5.5*M; // Star
      if(typ < 3.5) return 4.15*M; // Mass sphere
      return 4.6*M; // Planet visualization radius
    }
    float raySphere(vec3 ro, vec3 rd, vec3 center, float radius){
      vec3 oc=ro-center;
      float b=dot(oc,rd);
      float c=dot(oc,oc)-radius*radius;
      float h=b*b-c;
      if(h<0.0) return -1.0;
      float nearHit=-b-sqrt(h);
      return nearHit>0.0?nearHit:-b+sqrt(h);
    }
    vec3 newtonianScene(vec3 ro, vec3 rd, vec3 c1, vec3 c2, float m1, float m2, float fm1, float fm2, float t){
      vec3 color=sky(rd);
      float nearest=1e6;
      float nearestType=-1.0;
      vec3 nearestCenter=vec3(0.0);
      float radius1=radiusOf(uType1,m1);
      float radius2=radiusOf(uType2,m2);
      float hit1=raySphere(ro,rd,c1+vec3(0.0,radius1*0.82,0.0),radius1);
      float hit2=raySphere(ro,rd,c2+vec3(0.0,radius2*0.82,0.0),radius2);
      if(hit1>0.0){ nearest=hit1; nearestType=uType1; nearestCenter=c1+vec3(0.0,radius1*0.82,0.0); }
      if(hit2>0.0 && hit2<nearest){ nearest=hit2; nearestType=uType2; nearestCenter=c2+vec3(0.0,radius2*0.82,0.0); }

      if(rd.y < -0.015){
        float planeT=-ro.y/rd.y;
        if(planeT>0.0 && planeT<nearest){
          vec3 p=ro+rd*planeT;
          vec2 d1=p.xz-c1.xz;
          vec2 d2=p.xz-c2.xz;
          float r1=max(length(d1),0.1), r2=max(length(d2),0.1);
          vec2 warped=p.xz;
          warped-=d1*(fm1*0.72)/(r1+2.5);
          warped-=d2*(fm2*0.72)/(r2+2.5);
          vec2 cells=warped*0.28;
          float lineX=1.0-smoothstep(0.015,0.045,abs(fract(cells.x+0.5)-0.5));
          float lineZ=1.0-smoothstep(0.015,0.045,abs(fract(cells.y+0.5)-0.5));
          float grid=max(lineX,lineZ);
          float well1=fm1/sqrt(dot(d1,d1)+1.8);
          float well2=fm2/sqrt(dot(d2,d2)+1.8);
          float curvature=clamp(well1+well2,0.0,1.7);
          float contours=1.0-smoothstep(0.03,0.08,abs(fract((well1+well2)*2.2)-0.5));
          vec3 gridColor=mix(vec3(0.06,0.42,0.62),vec3(0.25,0.9,1.0),clamp(grid*0.7+curvature*0.35,0.0,1.0));
          color=vec3(0.003,0.008,0.017);
          color+=gridColor*grid*(0.18+0.55*curvature)*uGrid;
          color+=vec3(0.95,0.32,0.09)*contours*curvature*0.05;
          color+=vec3(0.02,0.32,0.48)*exp(-r1*0.11)*0.09;
          color+=vec3(0.18,0.78,0.64)*exp(-r2*0.11)*0.08;
          color+=sky(rd)*0.012;
        }
      }
      if(nearestType>=0.0){
        vec3 hit=ro+rd*nearest;
        vec3 normal=normalize(hit-nearestCenter);
        color=shadeBody(nearestType,normal)*(1.0-clamp(uMerger,0.0,1.0));
        float rim=pow(1.0-max(0.0,dot(normal,-rd)),3.0);
        color+=vec3(1.0,0.42,0.12)*rim*0.75*(1.0-clamp(uMerger,0.0,1.0));
      }
      if(uMerger>0.01){
        float remnantRadius=radiusOf(0.0,max(0.35*(m1+m2),0.3));
        float remnantT=raySphere(ro,rd,vec3(0.0,remnantRadius*0.82,0.0),remnantRadius);
        if(remnantT>0.0 && remnantT<nearest){
          nearest=remnantT;
          vec3 remnantPoint=ro+rd*remnantT;
          vec3 remnantNormal=normalize(remnantPoint-vec3(0.0,remnantRadius*0.82,0.0));
          color=vec3(0.001,0.002,0.006)+vec3(0.95,0.22,0.055)*pow(1.0-max(0.0,dot(remnantNormal,-rd)),5.0)*uMerger;
        }
        float impactFlash=exp(-pow((length(c1.xz)+length(c2.xz))*0.5-4.0,2.0)*0.16);
        color+=vec3(0.95,0.31,0.08)*impactFlash*uMerger*(1.0-uMerger)*0.3;
      }
      color+=0.035*color*color;
      color=color/(1.0+color);
      return pow(max(color,0.0),vec3(0.88));
    }
    float gridAt(vec3 p, vec3 c, float M){
      vec3 q=p-c;
      float rho=length(q.xz)/max(M,0.25);
      float phi=atan(q.z,q.x);
      // Spacetime curvature effect on grid
      float r=length(q);
      float curvature=2.0*M/max(r,2.0*M);
      float warpedRho=rho-curvature*0.3;
      float rings=1.0-smoothstep(0.0,0.05,abs(fract(warpedRho*0.32)-0.5)*2.0-1.0);
      float spokes=1.0-smoothstep(0.0,0.035,abs(sin(phi*6.0)));
      float plane=exp(-pow(q.y/(0.14*M),2.0));
      // Grid bends toward the black hole
      float bend=smoothstep(2.0*M,8.0*M,r);
      float fade=smoothstep(2.6,4.2,rho)*smoothstep(32.0,16.0,rho)*bend;
      return max(rings,spokes)*plane*fade;
    }

    void main(){
      vec2 uv=(gl_FragCoord.xy-0.5*iResolution)/iResolution.y;
      float M=1.0;
      float chi=clamp(uSpin,0.0,0.98);
      float t=iTime;
      float m1=max(uM1,0.35), m2=max(uM2,0.25);
      float q=m2/max(m1,1e-4);
      float sep=max(uSep,0.2);
      vec3 c1=vec3( sep*q/(1.0+q)*cos(uPhase), 0.0,  sep*q/(1.0+q)*sin(uPhase));
      vec3 c2=vec3(-sep/(1.0+q)*cos(uPhase), 0.0, -sep/(1.0+q)*sin(uPhase));
      if(uMerger>0.82){ c1=vec3(0.0); c2=c1; }

      float az=uCamAz, inc=clamp(uCamEl,0.18,1.52), Rcam=uCamDist;
      vec3 ro=vec3(Rcam*sin(inc)*sin(az), Rcam*cos(inc), Rcam*sin(inc)*cos(az));
      vec3 ww=normalize(-ro);
      vec3 uu=normalize(cross(ww, vec3(0.0,1.0,0.0)));
      vec3 vv=cross(uu,ww);
      vec3 rd=normalize(uv.x*uu+uv.y*vv+1.08*ww);

      if(uSimMode>0.5 && uCentralBH<0.5){
        vec3 flatColor=newtonianScene(ro,rd,c1,c2,m1,m2,uFieldM1,uFieldM2,t);
        flatColor+=(hash12(gl_FragCoord.xy)-0.5)*0.012;
        gl_FragColor=vec4(clamp(flatColor,0.0,1.0),1.0);
        return;
      }

      vec3 er=normalize(ro);
      vec3 tang=rd-er*dot(rd,er);
      float tangLen=length(tang);
      if(tangLen<1e-6){ gl_FragColor=vec4(0.0,0.0,0.0,1.0); return; }
      vec3 ephi=tang/tangLen;
      vec3 Lhat=normalize(cross(er,ephi));
      float r0=length(ro);
      float b=r0*tangLen;
      float u=1.0/r0;
      float wr=1.0/max(b*b,1e-8)-u*u+2.0*M*u*u*u;
      float dumag=sqrt(max(wr,0.0));
      float du=(dot(rd,er)<0.0)?dumag:-dumag;
      float phi=0.0;
      vec3 pos=ro, prev=ro;
      float captured=0.0, escaped=0.0;
      vec3 escapeDir=rd;
      vec3 col=vec3(0.0);
      float transm=1.0;
      const float DPHI=0.034;

      for(int i=0;i<200;i++){
        float h=DPHI;
        float u0=u, d0=du;
        float k1u=d0, k1d=3.0*M*u0*u0-u0;
        float k2u=d0+0.5*h*k1d; float u2=u0+0.5*h*k1u; float k2d=3.0*M*u2*u2-u2;
        float k3u=d0+0.5*h*k2d; float u3=u0+0.5*h*k2u; float k3d=3.0*M*u3*u3-u3;
        float k4u=d0+h*k3d;     float u4=u0+h*k3u;     float k4d=3.0*M*u4*u4-u4;
        u+=h*(k1u+2.0*k2u+2.0*k3u+k4u)/6.0;
        du+=h*(k1d+2.0*k2d+2.0*k3d+k4d)/6.0;
        phi+=h;
        float twist=chi*0.011*h;
        ephi=normalize(ephi*cos(twist)+cross(Lhat,ephi)*sin(twist));
        if(u<=1e-5){ escaped=1.0; break; }
        float r=1.0/u;
        prev=pos;
        pos=r*(cos(phi)*er+sin(phi)*ephi);
        vec3 dirp=pos-prev; float dl=length(dirp); vec3 nd=dirp/max(dl,1e-6);

        float rh1=radiusOf(uType1,m1);
        float rh2=radiusOf(uType2,m2);
        if(length(pos-c1)<rh1){
          if(uType1<0.5){ captured=1.0; break; }
          col+=transm*shadeBody(uType1, normalize(pos-c1))*2.4;
          transm*=0.06; break;
        }
        if(uMerger<0.82 && length(pos-c2)<rh2){
          if(uType2<0.5){ captured=1.0; break; }
          col+=transm*shadeBody(uType2, normalize(pos-c2))*2.4;
          transm*=0.06; break;
        }
        if(r<2.02*M && uMerger>0.7){ captured=1.0; break; }
        if(r>max(72.0*M,Rcam*1.15) && phi>0.45){ escaped=1.0; escapeDir=normalize(pos-prev); break; }

        vec3 emit=vec3(0.0);
        // Show accretion disk only in black hole mode (uSimMode < 0.5)
        if(uDisk>0.01 && uSimMode<0.5){
          if(uType1<0.5) emit+=diskAt(pos,nd,c1,m1,chi,t);
          if(uType2<0.5 && uMerger<0.82) emit+=diskAt(pos,nd,c2,m2,chi*0.85,t)*0.8;
          if(uMerger>0.55) emit+=diskAt(pos,nd,vec3(0.0),1.05,chi,t)*uMerger;
        }

        float g=0.0;
        if(uGrid>0.01){
          if(uSimMode>0.5 && uSimMode<1.5){
            // Newtonian collision: show the two-body gravity grid directly.
              g+=gridAt(pos,c1,uFieldM1);
              g+=gridAt(pos,c2,uFieldM2);
          } else {
            // Preserve the lensing scene's background and dual-object grid.
            g+=gridAt(pos,vec3(0.0),1.0);
            if(uMerger<0.82){
              g+=gridAt(pos,c1,uFieldM1)*0.45;
              g+=gridAt(pos,c2,uFieldM2)*0.45;
            }
          }
        }
        float ripple=0.5+0.5*sin(length(pos.xz)*1.2 - t*uWave*7.0);
        emit+=vec3(0.4,0.8,1.2)*g*uGrid*(0.3+0.85*ripple)*1.6;
        col+=transm*emit*dl*3.2;
        transm*=exp(-dl*0.012*length(emit));
        if(transm<0.012) break;
      }

      if(captured<0.5){
        vec3 bgd=escaped>0.5?escapeDir:normalize(pos);
        col+=transm*sky(bgd);
      }
      float bcrit=5.196152*(1.0-0.28*chi);
      col+=vec3(1.0,0.72,0.4)*exp(-pow((b-bcrit)*1.1,2.0)*16.0)*0.22*transm;
      col+=0.045*col*col;
      col=col/(1.0+col);
      col=pow(max(col,0.0), vec3(0.86));
      col+=(hash12(gl_FragCoord.xy)-0.5)*0.03;
      gl_FragColor=vec4(clamp(col,0.0,1.0),1.0);
    }
  `;

  const prog = gl.createProgram();
  gl.attachShader(prog, compile(vert, gl.VERTEX_SHADER));
  gl.attachShader(prog, compile(frag, gl.FRAGMENT_SHADER));
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog) || "link");
  gl.useProgram(prog);
  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(prog, "p");
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

  const U = {};
  ["iResolution","iTime","uSpin","uGrid","uDisk","uSep","uPhase","uM1","uM2","uFieldM1","uFieldM2","uType1","uType2","uWave","uMerger","uSimMode","uCentralBH","uCamAz","uCamEl","uCamDist"].forEach((k) => {
    U[k] = gl.getUniformLocation(prog, k);
  });

  const state = {
    spin: 0.7, grid: 0.7, disk: 0.85, sep: 11.0, phase: 0.0, m1: 1.0, m2: 0.8,
    fieldM1: 1.0, fieldM2: 0.8,
    type1: 0, type2: 0, wave: 0, merger: 0, playing: true, speed: 1,
    camAz: 0.35, camEl: 1.38, camDist: 28.0, _driven: false, simTime: 0,
    simModeVal: 0.0,  // 0 = blackhole, 1 = collision, 2 = scattering
    centralBH: 1.0,
    // Target values for smooth damping
    targetCamAz: 0.35, targetCamEl: 1.38, targetCamDist: 28.0,
  };

  let dragging = false, button = 0, lx = 0, ly = 0;
  canvas.addEventListener("pointerdown", (e) => {
    dragging = true; button = e.button; lx = e.clientX; ly = e.clientY;
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointerup", () => { dragging = false; });
  canvas.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const dx = e.clientX - lx, dy = e.clientY - ly;
    lx = e.clientX; ly = e.clientY;
    if (button === 2 || e.shiftKey) {
      state.targetCamEl = Math.min(1.52, Math.max(0.18, state.targetCamEl + dy * 0.006));
    } else {
      state.targetCamAz += dx * 0.008;
      state.targetCamEl = Math.min(1.52, Math.max(0.18, state.targetCamEl + dy * 0.005));
    }
  });
  canvas.addEventListener("contextmenu", (e) => e.preventDefault());
  canvas.addEventListener("wheel", (e) => {
    e.preventDefault();
    state.targetCamDist = Math.min(180, Math.max(8, state.targetCamDist * (e.deltaY > 0 ? 1.12 : 0.89)));
  }, { passive: false });

  function frame(now) {
    const dpr = Math.min(1.2, window.devicePixelRatio || 1);
    const w = Math.max(64, Math.floor(canvas.clientWidth * dpr));
    const h = Math.max(64, Math.floor(canvas.clientHeight * dpr));
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    gl.viewport(0, 0, w, h);
    const dt = Math.min(0.05, (now - (frame._last || now)) / 1000);
    frame._last = now;
    if (state.playing) {
      state.simTime += dt * state.speed;
      if (!state._driven) state.phase += dt * state.speed * 0.28;
    }
    // Smooth camera damping
    const damping = 8.0 * dt;
    state.camAz += (state.targetCamAz - state.camAz) * damping;
    state.camEl += (state.targetCamEl - state.camEl) * damping;
    state.camDist += (state.targetCamDist - state.camDist) * damping;
    gl.uniform2f(U.iResolution, w, h);
    gl.uniform1f(U.iTime, state.simTime);
    gl.uniform1f(U.uSpin, state.spin);
    gl.uniform1f(U.uGrid, state.grid);
    gl.uniform1f(U.uDisk, state.disk);
    gl.uniform1f(U.uSep, state.sep);
    gl.uniform1f(U.uPhase, state.phase);
    gl.uniform1f(U.uM1, state.m1);
    gl.uniform1f(U.uM2, state.m2);
    gl.uniform1f(U.uFieldM1, state.fieldM1);
    gl.uniform1f(U.uFieldM2, state.fieldM2);
    gl.uniform1f(U.uType1, state.type1);
    gl.uniform1f(U.uType2, state.type2);
    gl.uniform1f(U.uWave, state.wave);
    gl.uniform1f(U.uMerger, state.merger);
    gl.uniform1f(U.uSimMode, state.simModeVal);
    gl.uniform1f(U.uCentralBH, state.centralBH);
    gl.uniform1f(U.uCamAz, state.camAz);
    gl.uniform1f(U.uCamEl, state.camEl);
    gl.uniform1f(U.uCamDist, state.camDist);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  return state;
}
window.createBlackHoleRenderer = createBlackHoleRenderer;
