// Copyright (c) 2026, Rhocom Technology Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Hotel Profile', {
  refresh: function (frm) {
    remove_template_picker(frm);
    render_template_picker(frm);
  },

  active_template: function (frm) {
    remove_template_picker(frm);
    render_template_picker(frm);
  }
});

function remove_template_picker(frm) {
  if (!frm.fields_dict.active_template) return;

  frm.fields_dict.active_template
    .$wrapper
    .find('.template-picker-wrapper')
    .remove();
}

function render_template_picker(frm) {
  if (!frm.fields_dict.active_template) return;

  frappe.call({
    method: 'frappe.client.get_list',
    args: {
      doctype: 'Hotel Template',
      filters: { is_active: 1 },
      fields: [
        'name',
        'template_name',
        'template_code',
        'preview_image',
        'preview_video',
        'description'
      ],
      order_by: 'creation asc'
    },
    callback: function (r) {
      if (!r.message || !r.message.length) return;

      const templates = r.message;
      const current = frm.doc.active_template;

      if (!document.getElementById('templatePreviewModal')) {
        $('body').append(`
          <div id="templatePreviewModal" style="
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,.85);
            z-index: 9999;
            align-items: center;
            justify-content: center;
            padding: 2rem;
          ">
            <div style="
              background: #fff;
              border-radius: 16px;
              max-width: 950px;
              width: 100%;
              overflow: hidden;
              position: relative;
            ">
              <div style="
                padding: 1.25rem 1.5rem;
                border-bottom: 1px solid #e2e8f0;
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 1rem;
              ">
                <div>
                  <div id="modalTemplateName" style="
                    font-weight: 700;
                    font-size: 1.1rem;
                    color: #1a202c;
                  "></div>

                  <div id="modalTemplateDesc" style="
                    font-size: .85rem;
                    color: #718096;
                    margin-top: .2rem;
                  "></div>
                </div>

                <div style="display:flex; gap:.75rem; align-items:center;">
                  <button id="modalSelectBtn" style="
                    background: #2490ef;
                    color: #fff;
                    border: none;
                    padding: .6rem 1.5rem;
                    border-radius: 8px;
                    font-weight: 700;
                    cursor: pointer;
                    font-size: .9rem;
                    white-space: nowrap;
                  ">Use This Template</button>

                  <button id="modalCloseBtn" style="
                    background: #f1f5f9;
                    border: none;
                    width: 36px;
                    height: 36px;
                    border-radius: 50%;
                    font-size: 1.1rem;
                    cursor: pointer;
                    color: #64748b;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                  ">✕</button>
                </div>
              </div>

              <div style="
                max-height: 75vh;
                overflow-y: auto;
                background: #f8fafc;
              ">
                <video
                  id="modalPreviewVideo"
                  controls
                  playsinline
                  style="
                    width: 100%;
                    display: none;
                    background: #000;
                  "
                >
                  <source id="modalPreviewVideoSource" src="" type="video/mp4">
                  Your browser does not support the video tag.
                </video>

                <img id="modalPreviewImage" src="" alt="Template Preview" style="
                  width: 100%;
                  display: none;
                "/>

                <div id="modalNoPreview" style="
                  display: none;
                  padding: 4rem;
                  text-align: center;
                  color: #94a3b8;
                  font-size: 1rem;
                ">
                  📷 No preview image or video available for this template
                </div>
              </div>
            </div>
          </div>
        `);

        $('#modalCloseBtn').on('click', function () {
          close_template_preview_modal();
        });

        $('#templatePreviewModal').on('click', function (e) {
          if (e.target === this) {
            close_template_preview_modal();
          }
        });

        $(document).on('keydown.templatePreviewModal', function (e) {
          if (e.key === 'Escape') {
            close_template_preview_modal();
          }
        });
      }

      let html = `
        <div class="template-picker-wrapper" style="margin-top: 1rem;">
          <div style="
            margin-bottom: .75rem;
            font-weight: 700;
            color: #1f2937;
          ">
            Choose Website Template
          </div>

          <div style="
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
          ">
      `;

      templates.forEach(t => {
        const selected = current === t.name;
        const hasVideo = !!t.preview_video;
        const hasImage = !!t.preview_image;

        html += `
          <div class="template-card" data-template="${frappe.utils.escape_html(t.name)}" style="
            border: 3px solid ${selected ? '#2490ef' : '#e2e8f0'};
            border-radius: 12px;
            overflow: hidden;
            background: ${selected ? '#f0f7ff' : '#fff'};
            box-shadow: ${selected ? '0 4px 16px rgba(36,144,239,.2)' : '0 2px 8px rgba(0,0,0,.06)'};
            transition: all .2s;
          ">
            <div style="position: relative;">
              ${
                hasImage
                  ? `<img
                      src="${frappe.utils.escape_html(t.preview_image)}"
                      style="
                        width: 100%;
                        height: 140px;
                        object-fit: cover;
                        object-position: top;
                        display: block;
                      "
                    >`
                  : `<div style="
                      width: 100%;
                      height: 140px;
                      background: linear-gradient(135deg, #667eea, #764ba2);
                      display: flex;
                      align-items: center;
                      justify-content: center;
                      font-size: 2.5rem;
                    ">🏨</div>`
              }

              ${
                hasVideo
                  ? `<div style="
                      position: absolute;
                      left: 8px;
                      top: 8px;
                      background: rgba(220,38,38,.9);
                      color: #fff;
                      border-radius: 999px;
                      padding: .25rem .65rem;
                      font-size: .7rem;
                      font-weight: 700;
                    ">▶ Video</div>`
                  : ''
              }

              <button
                type="button"
                class="preview-template-btn"
                data-name="${frappe.utils.escape_html(t.name)}"
                data-image="${frappe.utils.escape_html(t.preview_image || '')}"
                data-video="${frappe.utils.escape_html(t.preview_video || '')}"
                data-template-name="${frappe.utils.escape_html(t.template_name || t.name)}"
                data-description="${frappe.utils.escape_html(t.description || '')}"
                style="
                  position: absolute;
                  top: 8px;
                  right: 8px;
                  background: rgba(0,0,0,.65);
                  color: #fff;
                  border: none;
                  border-radius: 6px;
                  padding: .35rem .75rem;
                  font-size: .75rem;
                  cursor: pointer;
                  backdrop-filter: blur(4px);
                "
              >👁 Preview</button>
            </div>

            <div style="padding: .85rem 1rem;">
              <div style="
                font-weight: 700;
                font-size: .95rem;
                color: ${selected ? '#2490ef' : '#1a202c'};
                margin-bottom: .2rem;
              ">
                ${frappe.utils.escape_html(t.template_name || t.name)}
              </div>

              <div style="
                font-size: .78rem;
                color: #718096;
                line-height: 1.4;
                margin-bottom: .6rem;
                min-height: 34px;
              ">
                ${frappe.utils.escape_html(t.description || '')}
              </div>

              <button
                type="button"
                class="select-template-btn"
                data-name="${frappe.utils.escape_html(t.name)}"
                style="
                  background: ${selected ? '#2490ef' : '#f1f5f9'};
                  color: ${selected ? '#fff' : '#374151'};
                  border: none;
                  padding: .45rem .9rem;
                  border-radius: 6px;
                  font-size: .8rem;
                  font-weight: 700;
                  cursor: pointer;
                  width: 100%;
                "
              >
                ${selected ? '✅ Selected' : 'Select Template'}
              </button>
            </div>
          </div>
        `;
      });

      html += `
          </div>
        </div>
      `;

      const $wrapper = frm.fields_dict.active_template.$wrapper;
      $wrapper.find('.template-picker-wrapper').remove();

      const $picker = $(html);

      $picker.on('click', '.select-template-btn', function () {
        const name = $(this).data('name');
        frm.set_value('active_template', name);
        frm.dirty();

        remove_template_picker(frm);
        render_template_picker(frm);
      });

      $picker.on('click', '.preview-template-btn', function (e) {
        e.stopPropagation();

        const image = $(this).data('image');
        const video = $(this).data('video');
        const name = $(this).data('template-name');
        const desc = $(this).data('description');
        const templateName = $(this).data('name');

        $('#modalTemplateName').text(name || '');
        $('#modalTemplateDesc').text(desc || '');

        show_template_preview_media(video, image);

        $('#modalSelectBtn').off('click').on('click', function () {
          frm.set_value('active_template', templateName);
          frm.dirty();

          close_template_preview_modal();

          remove_template_picker(frm);
          render_template_picker(frm);
        });

        $('#templatePreviewModal').css('display', 'flex');
      });

      $wrapper.append($picker);
    }
  });
}

function show_template_preview_media(video, image) {
  const $video = $('#modalPreviewVideo');
  const $videoSource = $('#modalPreviewVideoSource');
  const $image = $('#modalPreviewImage');
  const $empty = $('#modalNoPreview');

  $video.hide();
  $image.hide();
  $empty.hide();

  $video.get(0).pause();
  $videoSource.attr('src', '');
  $video.get(0).load();

  if (video) {
    $videoSource.attr('src', video);
    $video.get(0).load();
    $video.show();
    return;
  }

  if (image) {
    $image.attr('src', image).show();
    return;
  }

  $empty.show();
}

function close_template_preview_modal() {
  const video = document.getElementById('modalPreviewVideo');

  if (video) {
    video.pause();
    video.currentTime = 0;
  }

  $('#templatePreviewModal').hide();
}