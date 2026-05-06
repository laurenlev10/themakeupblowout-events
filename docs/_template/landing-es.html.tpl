<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The Makeup Blowout Sale — {{CITY}} {{YEAR}} — Español</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Josefin+Sans:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.9.0/css/all.css">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Josefin Sans', Helvetica, sans-serif; background: #000; color: #fff; min-height: 100vh; }
    .hero {
      background: linear-gradient(135deg, #1a0030 0%, #2d0050 50%, #1a1060 100%);
      padding: 40px 20px 30px; text-align: center;
    }
    .hero h1 { font-size: clamp(28px, 6vw, 52px); font-weight: 700; color: #f5e45b; line-height: 1.2; margin-bottom: 10px; }
    .hero .tagline { font-size: clamp(16px, 3vw, 22px); color: #f01070; margin-bottom: 8px; }
    .hero .free-entry { font-size: clamp(18px, 3.5vw, 26px); font-weight: 700; color: #fff; margin-top: 10px; }
    .live-counter {
      background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 12px 20px;
      margin: 20px auto; max-width: 500px; display: flex; align-items: center; justify-content: space-between; gap: 12px;
    }
    .live-counter .lc-live { display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; white-space: nowrap; }
    .live-counter .lc-dot { width: 8px; height: 8px; background: #22c55e; border-radius: 50%; animation: pulse 1s infinite; flex-shrink: 0; }
    .live-counter .lc-right { text-align: right; }
    .live-counter .lc-num { font-size: 26px; font-weight: 700; display: block; line-height: 1.1; }
    .live-counter .lc-text { font-size: 12px; color: #aaa; margin-top: 2px; }
    @keyframes pulse { 0%,100%{opacity:1;transform:scale(1);} 50%{opacity:.3;transform:scale(1.4);} }
    .event-details { background: #111; padding: 30px 20px; }
    .event-details ul { list-style: none; max-width: 600px; margin: 0 auto; }
    .event-details ul li { font-size: clamp(16px, 3vw, 20px); color: #ffcfd2; margin-top: 16px; line-height: 1.5; display: flex; align-items: flex-start; gap: 12px; }
    .event-details ul li i { color: #f01070; margin-top: 3px; flex-shrink: 0; }
    .sms-section { padding: 30px 20px; background: #000; }
    .sms-section h2 { text-align: center; font-size: clamp(20px, 4vw, 32px); color: #fff; margin-bottom: 6px; }
    .sms-section .sub { text-align: center; font-size: 15px; color: #aaa; margin-bottom: 20px; }
    .st-signupform {
      font-family: 'Josefin Sans', sans-serif; background: #f01070; max-width: 420px; border-radius: 8px;
      padding: 24px; margin: 0 auto; box-shadow: 0 8px 32px rgba(240,16,112,0.3);
    }
    .st-signupform input[type="text"] {
      width: 100%; background: #fff; border: 1px solid rgba(0,27,72,0.32); border-radius: 4px;
      padding: 10px 12px; font-size: 15px; font-family: inherit; margin-bottom: 14px; outline: none;
    }
    .st-signupform input[type="submit"] {
      width: 100%; background: linear-gradient(to bottom, #4527A0, #432D85); color: #fff; border: none;
      border-radius: 4px; padding: 12px; font-size: 16px; font-family: inherit; font-weight: 700; cursor: pointer; margin-top: 8px;
    }
    .st-signupform input[type="submit"]:hover { opacity: .9; }
    .st-font-caption { font-size: 11px; color: rgba(255,255,255,0.85); line-height: 1.5; display: flex; align-items: flex-start; gap: 8px; margin-bottom: 10px; }
    .st-font-caption input[type="checkbox"] { width: 16px; height: 16px; flex-shrink: 0; margin-top: 2px; }
    .st-font-caption a { color: #fff; }
    .st-hidden { display: none; }
    .st-color-red { color: #ff6b6b; font-size: 12px; }
    .step2-singleOptIn p { color: #fff; font-size: 20px; text-align: center; font-weight: 700; }
    .step2-doubleOptIn p { color: #fff; font-size: 15px; text-align: center; }
    .share-section { padding: 30px 20px; background: #0a0a0a; text-align: center; }
    .share-section h3 { font-size: clamp(18px, 3.5vw, 26px); color: #4267b2; margin-bottom: 16px; }
    .ig-btn {
      display: block; max-width: 420px; margin: 0 auto; background: #f01070; color: #fff !important;
      font-size: 18px; font-weight: 700; font-family: 'Josefin Sans', sans-serif; padding: 16px 28px;
      border-radius: 8px; text-decoration: none; box-shadow: 0 8px 24px rgba(240,16,112,0.4);
      transition: transform .2s, box-shadow .2s;
    }
    .ig-btn:hover { transform: translateY(-2px); box-shadow: 0 12px 30px rgba(240,16,112,0.5); }
    .ig-btn i { margin-right: 8px; }
    .countdown-section { padding: 24px 20px; background: #000; text-align: center; }
    .countdown-section .cd-label { font-size: clamp(16px, 3vw, 22px); color: #f01070; margin-bottom: 12px; }
    .countdown { display: flex; justify-content: center; gap: 20px; }
    .cd-block { text-align: center; min-width: 60px; }
    .cd-num { font-size: clamp(32px, 7vw, 48px); font-weight: 700; color: #fff; line-height: 1; }
    .cd-unit { font-size: 11px; color: #888; text-transform: uppercase; margin-top: 4px; }
    footer { text-align: center; padding: 20px; font-size: 12px; color: #444; background: #000; }

    /* === Image-section styling (added when Lauren's assets shipped) === */
    .hero {
      padding: 0 !important;
      background: #000 !important;
      position: relative;
    }
    .hero-img-wrap { position: relative; width: 100%; max-width: 720px; margin: 0 auto; }
    .hero-img-wrap img {
      width: 100%; height: auto; display: block;
    }
    .hero-text-overlay {
      padding: 28px 20px 24px;
      background: linear-gradient(135deg, #1a0030 0%, #2d0050 50%, #1a1060 100%);
      text-align: center;
    }
    .vendors-section {
      background: #fff;
      padding: 24px 16px;
      text-align: center;
    }
    .vendors-section img { max-width: 600px; width: 100%; height: auto; display: block; margin: 0 auto; }
    .vendors-section .vendors-caption {
      color: #1f2937; font-weight: 700; font-size: 14px; letter-spacing: 0.5px;
      margin-top: 10px; text-transform: uppercase;
    }
    .gift-media {
      max-width: 380px; width: 100%; margin: 0 auto 18px; display: block;
      border-radius: 12px; overflow: hidden;
      box-shadow: 0 8px 28px rgba(240,16,112,0.35);
    }
    .gift-media video, .gift-media img {
      width: 100%; height: auto; display: block;
    }
    .share-pic-wrap {
      max-width: 380px; margin: 0 auto 16px;
    }
    .share-pic-wrap img { width: 100%; height: auto; display: block; border-radius: 12px; }
    .limited-badge-wrap { text-align: center; margin-bottom: 8px; }
    .limited-badge-wrap img { max-width: 200px; width: 60%; height: auto; }
  </style>
</head>
<body>
  <div style="position:fixed;top:10px;right:12px;z-index:1000;display:flex;gap:6px;background:rgba(0,0,0,0.6);padding:6px 10px;border-radius:999px;backdrop-filter:blur(4px);">
    <a href="index.html" style="color:rgba(255,255,255,0.55);text-decoration:none;font-size:13px;font-weight:700;">EN</a>
    <span style="color:rgba(255,255,255,0.3);">|</span>
    <a href="index-es.html" style="color:#fff;text-decoration:none;font-size:13px;font-weight:700;">ES</a>
  </div>


  <section class="hero">
    <div class="hero-img-wrap">
      <img src="{{HERO_IMAGE}}" alt="The Makeup Blowout Sale - {{CITY}} - {{MONTH}} {{START_DAY}}-{{END_DAY}}, {{YEAR}}">
    </div>
    <div class="hero-text-overlay">
      <h1>&iexcl;Recibe Tu Glitter Fabuloso GRATIS! &#x2728;<br>{{CITY}}</h1>
      <p class="tagline">&iexcl;Prep&aacute;rate para un fin de semana fabuloso de belleza y ahorros!<br>&iexcl;40+ marcas incre&iacute;bles a precios imbatibles!</p>
      <p class="free-entry">&#x1F389; ENTRADA Y ESTACIONAMIENTO GRATIS</p>
    </div>
  </section>

  <div style="padding: 0 20px;">
    <div class="live-counter">
      <div class="lc-live"><span class="lc-dot"></span>EN VIVO</div>
      <div class="lc-right">
        <span class="lc-num" id="lc-num">1,247</span>
        <div class="lc-text">Bellezas registradas para este evento</div>
      </div>
    </div>
  </div>

  <section class="event-details">
    <ul>
      <li>
        <i class="fas fa-calendar-alt"></i>
        <span>Viernes - Domingo,<br>{{MONTH}} {{START_DAY}} &#x2013; {{MONTH}} {{END_DAY}}, {{YEAR}}<br><strong>10am &#x2013; 5pm</strong></span>
      </li>
      <li>
        <i class="fas fa-map-marker-alt"></i>
        <span>{{STREET}}<br>At {{HOTEL}}</span>
      </li>
      <li>
        <i class="fas fa-tag"></i>
        <span>&iexcl;ENTRADA Y ESTACIONAMIENTO GRATIS &#x2014; No se necesitan boletos!</span>
      </li>
    </ul>
  </section>

  <section class="sms-section">
    <div class="gift-media">
      <img src="/_assets/shared/NEW%20GIF.gif" alt="Free Glitter Gift">
    </div>
    <h2>&#x1F381; &iexcl;Reclama Tu Regalo GRATIS!</h2>
    <p class="sub">Reg&iacute;strate por SMS y recibe un cup&oacute;n de glitter GRATIS</p>

    <script>
    (function joinWebForm(
      win, doc, formId,
      DUPLICATE_PHONE_EXCEPTION, DUPLICATE_EMAIL_EXCEPTION, CUSTOM_FIELDS_VALIDATION_EXCEPTION,
      doubleOptIn
    ) {
      var XHR = ('onload' in new win.XMLHttpRequest()) ? win.XMLHttpRequest : win.XDomainRequest;
      var form;
      var formServerErrorMessage;
      var formTermsAgreedError;
      var fieldErrorClassName = 'st-signupform-validation-error';
      function setServerErrorMessage(message){ formServerErrorMessage.innerText = message; }
      function isTermsAgreedAccepted(){ return form.querySelector('input[name="terms-agreed"]').checked; }
      function showTermsAgreedError(){ formTermsAgreedError.style.display = 'block'; }
      function hideTermsAgreedError(){ formTermsAgreedError.style.display = 'none'; }
      function clearFormErrors(){
        var fields = form.querySelectorAll('.' + fieldErrorClassName);
        Array.prototype.slice.call(fields).forEach(function(field){
          field.className = field.className.split(/\s/).filter(function(c){return c !== fieldErrorClassName && c;}).join(' ');
        });
        setServerErrorMessage('');
        hideTermsAgreedError();
      }
      function collectFormData(){
        var data = {};
        Array.prototype.slice.call(form).forEach(function(field){ data[field.name] = field.value; });
        return data;
      }
      function parseServerValidationError(response){
        var result = {};
        try {
          var error = win.JSON.parse(response);
          if (error.code === DUPLICATE_PHONE_EXCEPTION) { result.fieldName = 'phone'; result.errorMessage = 'El n&uacute;mero ya existe.'; }
          else if (error.code === DUPLICATE_EMAIL_EXCEPTION) { result.fieldName = 'email'; result.errorMessage = 'El correo ya existe.'; }
          else if (error.code === CUSTOM_FIELDS_VALIDATION_EXCEPTION) { result.fieldName = error.reasons[0].field; result.errorMessage = error.reasons[0].reason; }
          else { result.fieldName = error.field; result.errorMessage = error.reason; }
        } catch(_){}
        result.fieldName = result.fieldName || '';
        result.errorMessage = result.errorMessage || 'Error de validaci&oacute;n.';
        return result;
      }
      function handleLoadForm(){
        var validation, field;
        if (this.status === 200) {
          form.querySelector('.step1-form').style.display = 'none';
          // Redirect to per-event share/thank-you page
          document.location.href = 'share-es.html';
          form.reset();
        } else if (this.status === 418) {
          validation = parseServerValidationError(this.responseText);
          if (validation.fieldName) {
            field = form.querySelector('input[name="' + validation.fieldName + '"]');
            if (field) field.className += ' ' + fieldErrorClassName;
          }
          setServerErrorMessage(validation.errorMessage);
        } else {
          setServerErrorMessage('Error interno. Int&eacute;ntalo m&aacute;s tarde.');
        }
      }
      function handleErrorForm(){ setServerErrorMessage('Error interno. Int&eacute;ntalo m&aacute;s tarde.'); }
      function sendForm(){
        var data = collectFormData();
        var url = 'https://app2.simpletexting.com/join/joinContact?r=' + Date.now();
        var request = new XHR();
        request.open(form.method, url);
        request.onload = handleLoadForm;
        request.onerror = handleErrorForm;
        request.ontimeout = handleErrorForm;
        try { request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8'); } catch(_){}
        request.send(win.JSON.stringify(data));
      }
      function handleSubmitForm(event){
        event.preventDefault();
        clearFormErrors();
        if (!isTermsAgreedAccepted()) { showTermsAgreedError(); }
        else { sendForm(); }
        return false;
      }
      function formatPhone(value){
        var numbers = value.replace(/\D/g, '');
        var firstPart = numbers.substring(0, 3);
        var secondPart = numbers.substring(3, 6);
        var thirdPart = numbers.substring(6, 10);
        var result = '';
        if (firstPart) { result += '(' + firstPart; }
        if (secondPart) { result += ') ' + secondPart; }
        if (thirdPart) { result += '-' + thirdPart; }
        return result;
      }
      function handleChangePhoneField(event){ var f = event.currentTarget; f.value = formatPhone(f.value); }
      function handleLoad(){
        form = doc.getElementById(formId);
        if (!form) return;
        formServerErrorMessage = form.querySelector('.st-signupform-server-error-message');
        formTermsAgreedError = form.querySelector('.st-signupform-terms-agreed-error');
        var phoneFields = form.querySelectorAll('input[data-type="phone"]');
        form.addEventListener('submit', handleSubmitForm);
        Array.prototype.slice.call(phoneFields).forEach(function(field){
          field.addEventListener('input', handleChangePhoneField);
        });
      }
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', handleLoad);
      } else {
        handleLoad();
      }
    })(
      window, document, 'st-join-web-form-{{FORM_ID}}',
      'DuplicateContactPhoneException', 'DuplicateContactEmailException', 'CustomFieldsValidationException'
    );
    </script>

    <form id="st-join-web-form-{{FORM_ID}}" class="st-signupform" action="https://app2.simpletexting.com/join/joinContact" method="POST">
      <div class="step1-form">
        <input type="hidden" name="webFormId" value="{{FORM_ID}}" id="webFormId-{{FORM_ID}}">
        <input type="hidden" name="country" value="USA" id="country-{{FORM_ID}}">
        <div class="required" style="text-align: center">
          <input id="phone-{{FORM_ID}}" name="phone" type="text" placeholder="Tu N&uacute;mero de Tel&eacute;fono" maxlength="1600" data-type="phone" class="phoneNumber" required>
        </div>
        <div class="st-font-caption">
          <input id="terms-agreed-checkbox-{{FORM_ID}}" type="checkbox" name="terms-agreed" checked>
          <label for="terms-agreed-checkbox-{{FORM_ID}}">Al suscribirte aceptas recibir mensajes de texto de marketing automatizados. El consentimiento no es requerido para la compra. Pueden aplicar tarifas de mensajes y datos. Responde STOP para cancelar. <a href="https://app2.simpletexting.com/web-forms/terms/654d65258f51cb55a9016540" target="_blank">T&eacute;rminos</a></label>
        </div>
        <p class="st-signupform-terms-agreed-error st-color-red st-hidden">Acepta los t&eacute;rminos para continuar.</p>
        <div class="st-join-web-form-submit-button-box">
          <input type="submit" value="&#x2709;&#xFE0F; ENV&Iacute;AME MI CUP&Oacute;N" name="subscribe">
          <p class="st-signupform-server-error-message st-color-red">&nbsp;</p>
        </div>
      </div>
      <div class="step2-singleOptIn st-hidden">
        <p>&#x1F389; &iexcl;Tu cup&oacute;n viene en camino! &iexcl;Comp&aacute;rtelo en tu historia y recibe una sombra GRATIS!</p>
      </div>
    </form>
  </section>


  <section class="vendors-section">
    <img src="/_assets/shared/Vendors-Logos.png" alt="40+ Top Beauty Brands">
    <div class="vendors-caption">40+ MARCAS TOP &#x2022; HASTA 75% DE DESCUENTO</div>
  </section>







  <section class="promo-collage" style="background:#fdf2f8;padding:24px 16px;text-align:center;">
    <img src="/_assets/shared/75-OFF-1-.png" alt="75% off Makeup, Skincare &amp; Hair Care" style="max-width:480px;width:100%;height:auto;border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,0.08);">
    <p style="margin:14px 0 0;color:#1f2937;font-weight:700;font-size:14px;letter-spacing:0.5px;text-transform:uppercase;">&iexcl;HASTA 75% DE DESCUENTO &mdash; NO TE LO PUEDES PERDER!</p>
  </section>

  <footer>
    &copy; {{YEAR}} The Makeup Blowout Sale Group. All rights reserved.
  </footer>

  <script>
    (function(){
      var sc=1200+Math.floor(Math.random()*80);
      function fmt(n){return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g,',');}
      var el=document.getElementById('lc-num');
      if(el){el.textContent=fmt(sc);}
      function bump(){sc+=Math.floor(Math.random()*3)+1;if(el){el.textContent=fmt(sc);}setTimeout(bump,8000+Math.floor(Math.random()*5000));}
      setTimeout(bump,8000+Math.floor(Math.random()*5000));
    })();
  </script>

</body>
</html>
