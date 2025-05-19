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
  const rule = mockRules.find((r) => r.rule_id === rule_id);
  if (!rule) return;
  const newDrop = confirm("是否要丟棄封包？");
  if (newDrop) {
    updateRule(rule_id, rule.country_code, 0, true);
  } else {
    const newDelay = prompt("請輸入新的延遲百分比", rule.delay_percentage);
    if (newDelay === null) return;
    updateRule(rule_id, rule.country_code, parseInt(newDelay), false);
  }
}

function updateRule(rule_id, country_code, delay_percentage, drop) {
  const body = JSON.stringify({ country_code, delay_percentage, drop });
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
  const mockPackets = [
    {
      packet_id: "abc123",
      source_ip: "192.0.2.1",
      source_country: "US",
      destination_ip: "192.0.2.5",
      destination_country: "US",
      timestamp: "2025-05-14T07:30:00Z",
      status: "delayed",
      applied_rule_id: 1,
    },
    {
      packet_id: "def456",
      source_ip: "203.0.113.5",
      source_country: "AU",
      destination_ip: "192.0.2.10",
      destination_country: "CN",
      timestamp: "2025-05-14T07:35:00Z",
      status: "dropped",
      applied_rule_id: 2,
    },
    {
      packet_id: "abc123",
      source_ip: "192.0.2.10",
      source_country: "TW",
      destination_ip: "192.0.2.100",
      destination_country: "US",
      timestamp: "2025-05-14T07:30:00Z",
      status: "delayed",
      applied_rule_id: 3,
    },
  ];
  displayPackets(mockPackets);
}

function displayPackets(packets) {
  const tbody = document.querySelector("#packet-table tbody");
  tbody.innerHTML = "";
  packets.forEach((p) => {
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
<td>${p.source_ip} <br>
<td><img src="${
      sourceInfo.flag
    }" style="width:20px;height:14px;vertical-align:middle;"> ${
      sourceInfo.name
    }</td>
<td>${p.destination_ip} <br>
<td><img src="${
      destInfo.flag
    }" style="width:20px;height:14px;vertical-align:middle;"> ${
      destInfo.name
    }</td>
<td>${new Date(p.timestamp).toLocaleString()}</td>
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
