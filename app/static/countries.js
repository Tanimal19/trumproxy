document.addEventListener("DOMContentLoaded", async () => {
  const select = document.getElementById("country-select");
  const flagDisplay = document.getElementById("flag-display");

  try {
    // 取得國家資料
    const res = await fetch("https://restcountries.com/v3.1/all");
    const countries = await res.json();

    // 排序並加入選單
    countries
      .sort((a, b) => a.name.common.localeCompare(b.name.common))
      .forEach((country) => {
        const option = document.createElement("option");
        option.value = country.cca2; // 2-letter country code
        option.textContent = country.name.common;
        option.dataset.flag = country.flags.svg;
        select.appendChild(option);
      });

    // 啟用 Tom Select
    const tomSelect = new TomSelect(select, {
      maxItems: 1,
      render: {
        option: function (data, escape) {
          return `<div>
                    <img src="${escape(
                      data.flag
                    )}" style="width:20px;height:15px;margin-right:5px;">
                    ${escape(data.text)}
                  </div>`;
        },
        item: function (data, escape) {
          return `<div>
                    <img src="${escape(
                      data.flag
                    )}" style="width:20px;height:15px;margin-right:5px;">
                    ${escape(data.text)}
                  </div>`;
        },
      },
      onChange: function (value) {
        const selected = this.options[value];
        if (selected && selected.flag) {
          flagDisplay.innerHTML = `
            <img src="${selected.flag}" alt="Flag" style="width:100px;">
            <p>${selected.text}</p>
          `;
        } else {
          flagDisplay.innerHTML = "";
        }
      },
    });

    // 將 flag URL 存入 TomSelect 的 options
    Object.values(tomSelect.options).forEach((opt) => {
      const optionEl = select.querySelector(`option[value="${opt.value}"]`);
      if (optionEl) {
        opt.flag = optionEl.dataset.flag;
      }
    });
  } catch (e) {
    console.error("載入國家資料失敗：", e);
    flagDisplay.textContent = "載入失敗，請稍後再試。";
  }
});

let mockRules = [
  { rule_id: 1, country_code: "US", delay_percentage: 30, drop: false },
  { rule_id: 2, country_code: "CN", delay_percentage: 100, drop: true },
];
let nextRuleId = 3;

function displayRules(rules) {
  const tbody = document.querySelector("#rules-table tbody");
  tbody.innerHTML = "";
  rules.forEach((rule) => {
    const countryInfo = countryMap[rule.country_code] || {
      name: rule.country_code,
      flag: "",
    };
    const displayText = rule.drop ? "丟棄" : `稅率 ${rule.delay_percentage}%`;
    const tr = document.createElement("tr");
    tr.innerHTML = `
<td><img src="${countryInfo.flag}" style="width:20px;height:14px;vertical-align:middle;"> ${countryInfo.name}</td>
<td colspan="2">${displayText}</td>
<td>
  <button onclick="editRule(${rule.rule_id})">修改</button>
  <button onclick="deleteRule(${rule.rule_id})">刪除</button>
</td>`;
    tbody.appendChild(tr);
  });
}

function fetchRules() {
  fetch("/api/rules", {
    method: "GET",
  })
    .then((res) => res.json())
    .then((data) => displayRules(data.rules))
    .catch(() => {
      console.warn("使用 mockRules 模擬規則列表");
      displayRules(mockRules);
    });
}

function addRule() {
  const country = document.getElementById("country-select").value;
  const drop = document.getElementById("drop-checkbox").checked;
  const delayInput = document.getElementById("delay-input");
  const delay = drop ? 0 : parseInt(delayInput.value);
  if (!country) return alert("請選擇國家");
  const body = JSON.stringify({
    country_code: country,
    delay_percentage: delay,
    drop,
  });
  fetch("/api/rules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  })
    .then((res) => (res.ok ? res.json() : Promise.reject()))
    .then(() => fetchRules())
    .catch(() => {
      console.warn("使用 mockRules 模擬新增");
      mockRules.push({
        rule_id: nextRuleId++,
        country_code: country,
        delay_percentage: delay,
        drop,
      });
      fetchRules();
    });
}

function editRule(rule_id) {
  // 先移除可能已存在的舊 modal
  const existingModal = document.getElementById("edit-rule-modal");
  if (existingModal) {
    existingModal.remove();
  }

  // 建立 modal 容器
  const modal = document.createElement("div");
  modal.id = "edit-rule-modal";
  modal.style.position = "fixed";
  modal.style.left = "50%";
  modal.style.top = "50%";
  modal.style.transform = "translate(-50%, -50%)";
  modal.style.backgroundColor = "white";
  modal.style.padding = "20px";
  modal.style.border = "1px solid #ccc";
  modal.style.borderRadius = "8px";
  modal.style.boxShadow = "0 4px 8px rgba(0,0,0,0.1)";
  modal.style.zIndex = "1000"; // 確保在最上層

  // Modal 內容
  modal.innerHTML = `
    <h3 style="margin-top:0;">編輯規則 (ID: ${rule_id})</h3>
    <div style="margin-bottom: 15px;">
      <label>
        <input type="checkbox" id="modal-drop-checkbox"> 丟棄封包 (Drop Packets)
      </label>
    </div>
    <div style="margin-bottom: 20px;">
      <label for="modal-delay-input">延遲百分比:</label>
      <input type="number" id="modal-delay-input" min="0" style="width: 80px; margin-left: 5px;">
    </div>
    <div style="text-align: right;">
      <button id="modal-confirm-button" style="margin-right: 10px; padding: 8px 15px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">確認</button>
      <button id="modal-cancel-button" style="padding: 8px 15px; background-color: #f44336; color: white; border: none; border-radius: 4px; cursor: pointer;">取消</button>
    </div>
  `;

  document.body.appendChild(modal);

  // 獲取 modal 內的元素
  const dropCheckbox = modal.querySelector("#modal-drop-checkbox");
  const delayInput = modal.querySelector("#modal-delay-input");
  const confirmButton = modal.querySelector("#modal-confirm-button");
  const cancelButton = modal.querySelector("#modal-cancel-button");

  // Drop checkbox 事件監聽
  dropCheckbox.addEventListener("change", function () {
    delayInput.disabled = this.checked;
    if (this.checked) {
      delayInput.value = ""; // 清空延遲值
    }
  });

  // 確認按鈕事件
  confirmButton.addEventListener("click", () => {
    const newDrop = dropCheckbox.checked;
    let newDelay = 0;

    if (!newDrop) {
      const delayValue = parseInt(delayInput.value, 10);
      if (isNaN(delayValue) || delayValue < 0) {
        alert("請輸入有效的延遲百分比");
        return;
      }
      newDelay = delayValue;
    }

    updateRule(rule_id, newDelay, newDrop);
    modal.remove(); // 關閉 modal
  });

  // 取消按鈕事件
  cancelButton.addEventListener("click", () => {
    modal.remove(); // 關閉 modal
  });

  // 可選：點擊 modal 外部關閉 (如果需要)
  // modal.addEventListener('click', function(event) {
  //   if (event.target === modal) {
  //     modal.remove();
  //   }
  // });
}

function updateRule(rule_id, delay_percentage, drop) {
  const body = JSON.stringify({
    delay_percentage: delay_percentage,
    drop,
  });
  fetch(`/api/rules/${rule_id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body,
  })
    .then((res) => (res.ok ? res.json() : Promise.reject()))
    .then(() => fetchRules())
    .catch(() => {
      console.warn("使用 mockRules 模擬修改");
      const rule = mockRules.find((r) => r.rule_id === rule_id);
      if (rule) {
        rule.delay_percentage = delay_percentage;
        rule.drop = drop;
      }
      fetchRules();
    });
}

function deleteRule(rule_id) {
  if (!confirm("確認刪除此規則？")) return;
  fetch(`/api/rules/${rule_id}`, {
    method: "DELETE",
  })
    .then((res) => (res.ok ? res.json() : Promise.reject()))
    .then(() => fetchRules())
    .catch(() => {
      console.warn("使用 mockRules 模擬刪除");
      mockRules = mockRules.filter((r) => r.rule_id !== rule_id);
      fetchRules();
    });
}

function fetchPackets() {
  fetch("/api/packets", {
    method: "GET",
  })
    .then((res) => res.json())
    .then((data) => displayPackets(data.packets))
}

function displayPackets(packets) {
  const tbody = document.querySelector("#packet-table tbody");
  tbody.innerHTML = "";
  packets.forEach((p) => {
    console.log(p);
    const sourceInfo = countryMap[p.source_country] || {
      name: p.source_country,
      flag: "",
    };
    const destInfo = countryMap[p.destination_country] || {
      name: p.destination_country,
      flag: "",
    };
    const statusText = p.status === "dropped" ? "丟棄" : "扣留中";
    const tr = document.createElement("tr");
    tr.innerHTML = `
<td>${p.packet_id}</td>
<td>${p.size}</td>
<td>${p.source_ip}</td>
<td><img src="${
      sourceInfo.flag
    }" style="width:20px;height:14px;vertical-align:middle;"> ${
      sourceInfo.name
    }</td>
<td>${new Date(p.timestamp).toLocaleString()}</td>
<td>${p.rtt_time}ms</td>
<td>${p.retain_time}s</td>
<td><span class="badge ${p.status}">${statusText}</span></td>`;
    tbody.appendChild(tr);
  });
}

let countryMap = {};
function loadCountryMap() {
  fetch("https://restcountries.com/v3.1/all")
    .then((res) => res.json())
    .then((countries) => {
      countries.forEach((c) => {
        countryMap[c.cca2] = {
          name: c.name.common,
          flag: c.flags.svg,
        };
      });
      fetchRules();
      fetchPackets();
    });
}

document
  .getElementById("drop-checkbox")
  .addEventListener("change", function () {
    document.getElementById("delay-input").disabled = this.checked;
  });

setInterval(fetchPackets, 5000);
loadCountryMap();
