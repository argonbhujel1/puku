/* Puku Kosheli Hub — Main JS */
(function () {
  'use strict';

  // CSRF token helper
  function getCsrf() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  // Mobile nav
  const hamburger = document.getElementById('hamburger');
  const mobileNav = document.getElementById('mobile-nav');
  if (hamburger && mobileNav) {
    hamburger.addEventListener('click', function () {
      mobileNav.classList.toggle('open');
      hamburger.setAttribute('aria-expanded', mobileNav.classList.contains('open'));
    });
  }

  // Hero jar mouse interaction (desktop only)
  const jar = document.getElementById('hero-jar');
  const heroVisual = document.querySelector('.hero-visual');
  if (jar && heroVisual && window.matchMedia('(min-width: 769px)').matches &&
      !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    heroVisual.addEventListener('mousemove', function (e) {
      const rect = heroVisual.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      jar.style.transform = `rotateY(${x * 20}deg) rotateX(${-y * 15}deg) translateY(-6px)`;
    });
    heroVisual.addEventListener('mouseleave', function () {
      jar.style.transform = '';
    });
  }

  // Scroll reveal
  const revealEls = document.querySelectorAll('.story-step, .why-card, .product-card, .review-card');
  if (revealEls.length && 'IntersectionObserver' in window) {
    const obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    revealEls.forEach(function (el) {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
      obs.observe(el);
    });
  }

  // Add to cart via fetch
  document.querySelectorAll('.btn-add-cart').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const productId = btn.dataset.productId;
      const qty = btn.dataset.qty || 1;
      if (!productId) return;

      btn.disabled = true;
      const original = btn.innerHTML;
      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

      const formData = new FormData();
      formData.append('product_id', productId);
      formData.append('quantity', qty);
      formData.append('csrf_token', getCsrf());

      fetch('/cart/add', {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.ok) {
            updateCartBadge(data.cart_count);
            showToast(data.message || 'झोलामा थपियो!');
          } else {
            showToast(data.error || 'त्रुटि भयो', true);
          }
        })
        .catch(function () {
          showToast('नेटवर्क त्रुटि', true);
        })
        .finally(function () {
          btn.disabled = false;
          btn.innerHTML = original;
        });
    });
  });

  function updateCartBadge(count) {
    document.querySelectorAll('.cart-badge').forEach(function (badge) {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    });
  }

  function showToast(msg, isError) {
    let toast = document.getElementById('toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'toast';
      toast.style.cssText = 'position:fixed;bottom:90px;left:50%;transform:translateX(-50%);padding:12px 24px;border-radius:50px;color:white;font-weight:600;z-index:3000;transition:opacity 0.3s;font-size:0.95rem;';
      document.body.appendChild(toast);
    }
    toast.style.background = isError ? '#c0392b' : '#2D5A27';
    toast.textContent = msg;
    toast.style.opacity = '1';
    setTimeout(function () { toast.style.opacity = '0'; }, 2500);
  }

  // Cart quantity controls
  document.querySelectorAll('.qty-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const row = btn.closest('[data-product-id]');
      if (!row) return;
      const pid = row.dataset.productId;
      const input = row.querySelector('.qty-input');
      let qty = parseInt(input.value, 10) || 1;
      if (btn.dataset.action === 'inc') qty++;
      if (btn.dataset.action === 'dec') qty--;
      if (qty < 0) qty = 0;
      input.value = qty;
      updateCartItem(pid, qty, row);
    });
  });

  function updateCartItem(productId, quantity, row) {
    const formData = new FormData();
    formData.append('product_id', productId);
    formData.append('quantity', quantity);
    formData.append('csrf_token', getCsrf());

    fetch('/cart/update', {
      method: 'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      body: formData
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.ok) {
          updateCartBadge(data.cart_count);
          const subEl = document.getElementById('cart-subtotal');
          const delEl = document.getElementById('cart-delivery');
          const totEl = document.getElementById('cart-total');
          if (subEl) subEl.textContent = 'रु. ' + Math.round(data.subtotal).toLocaleString();
          if (delEl) delEl.textContent = 'रु. ' + Math.round(data.delivery_charge).toLocaleString();
          if (totEl) totEl.textContent = 'रु. ' + Math.round(data.total).toLocaleString();
          if (quantity <= 0 && row) row.remove();
          if (data.cart_count === 0) window.location.reload();
        }
      });
  }

  // Remove from cart
  document.querySelectorAll('.btn-remove-cart').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const pid = btn.dataset.productId;
      const formData = new FormData();
      formData.append('product_id', pid);
      formData.append('csrf_token', getCsrf());
      fetch('/cart/remove', {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.ok) {
            const row = btn.closest('[data-product-id]');
            if (row) row.remove();
            updateCartBadge(data.cart_count);
            if (data.cart_count === 0) window.location.reload();
            else {
              const subEl = document.getElementById('cart-subtotal');
              const totEl = document.getElementById('cart-total');
              if (subEl) subEl.textContent = 'रु. ' + Math.round(data.subtotal).toLocaleString();
              if (totEl) totEl.textContent = 'रु. ' + Math.round(data.total).toLocaleString();
            }
          }
        });
    });
  });

  // Gallery lightbox
  document.querySelectorAll('.gallery-item img').forEach(function (img) {
    img.addEventListener('click', function () {
      let lb = document.getElementById('lightbox');
      if (!lb) {
        lb = document.createElement('div');
        lb.id = 'lightbox';
        lb.className = 'lightbox';
        lb.innerHTML = '<button class="lightbox-close" aria-label="बन्द">&times;</button><img src="" alt="">';
        document.body.appendChild(lb);
        lb.querySelector('.lightbox-close').addEventListener('click', function () {
          lb.classList.remove('open');
        });
        lb.addEventListener('click', function (e) {
          if (e.target === lb) lb.classList.remove('open');
        });
      }
      lb.querySelector('img').src = img.src;
      lb.classList.add('open');
    });
  });

  // Quantity selector on product detail
  const qtyInput = document.getElementById('product-qty');
  if (qtyInput) {
    document.querySelectorAll('.qty-detail-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        let v = parseInt(qtyInput.value, 10) || 1;
        if (btn.dataset.action === 'inc') v++;
        if (btn.dataset.action === 'dec') v = Math.max(1, v - 1);
        const max = parseInt(qtyInput.max, 10) || 99;
        if (v > max) v = max;
        qtyInput.value = v;
        const addBtn = document.querySelector('.btn-add-cart-detail');
        if (addBtn) addBtn.dataset.qty = v;
      });
    });
  }

  // Delivery method toggle on checkout
  const deliveryRadios = document.querySelectorAll('input[name="delivery_method"]');
  const addressFields = document.getElementById('address-fields');
  if (deliveryRadios.length && addressFields) {
    deliveryRadios.forEach(function (r) {
      r.addEventListener('change', function () {
        addressFields.style.display = r.value === 'delivery' ? 'block' : 'none';
      });
    });
  }
})();
