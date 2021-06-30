import credentials
import data_report_configs
import data_classification_vulnerability_types
import functions_source_ms_cve
import functions_source_nvd_cve
import functions_source_attackerkb_cve
import functions_source_vulners
import functions_tools
import functions_score
import re
import json
from datetime import datetime


def get_vuln_products(ms_cve_data_all):
    # Getting vulnerable products for CVE items
    all_vuln_products = set()
    for cve_id in ms_cve_data_all:
        if 'vuln_product' in ms_cve_data_all[cve_id]:
            all_vuln_products.add(ms_cve_data_all[cve_id]['vuln_product'])
        else:
            print("No vuln_product for item")
            print(ms_cve_data_all[cve_id])
    all_vuln_products = list(all_vuln_products)
    all_vuln_products.sort()
    return all_vuln_products


def get_vulnerability_types_priority(vulnerability_type_data):
    vulnerability_types_priority = list()
    criticalities = dict()
    for vuln_type in vulnerability_type_data:
        if not vulnerability_type_data[vuln_type]['criticality'] in criticalities:
            criticalities[vulnerability_type_data[vuln_type]['criticality']] = list()
        criticalities[vulnerability_type_data[vuln_type]['criticality']].append(vuln_type)
    criticality_keys = list(criticalities.keys())
    criticality_keys.sort(reverse=True)
    for criticality_key in criticality_keys:
        vuln_types = criticalities[criticality_key]
        vuln_types.sort()
        for vuln_type in vuln_types:
            vulnerability_types_priority.append(vuln_type)
    return vulnerability_types_priority


def get_vuln_types(ms_cve_data_all):
    # Getting vulnerability types for CVE items
    all_vuln_types = set()
    for cve_id in ms_cve_data_all:
        all_vuln_types.add(ms_cve_data_all[cve_id]['vuln_type'])
    all_vuln_types = list(all_vuln_types)
    all_vuln_types.sort()
    # Add types in order of vulnerability_types_priority
    prioritized_vuln_types = list()
    for vuln_type in get_vulnerability_types_priority(data_classification_vulnerability_types.vulnerability_type_data):
        if vuln_type in all_vuln_types:
            prioritized_vuln_types.append(vuln_type)
    # Add other types in alphabetical order
    for vuln_type in all_vuln_types:
        if vuln_type not in prioritized_vuln_types:
            prioritized_vuln_types.append(vuln_type)
    return prioritized_vuln_types


def get_vulns_filtered_by_wild_exploited(exploited, current_cve_data, cve_scores):
    vulnerabilities = dict()
    for cve_id in current_cve_data:
        wild_exploited = False
        if cve_scores[cve_id]['components']['Exploited in the Wild']['value'] == 1:
            wild_exploited = True
        if wild_exploited == True and exploited == "Yes":
            vulnerabilities[cve_id] = current_cve_data[cve_id]
        elif wild_exploited == False and exploited == "No":
            vulnerabilities[cve_id] = current_cve_data[cve_id]
    return vulnerabilities


def get_vulns_filtered_by_public_exploit_exists(public_exploit_exists, current_cve_data, cve_scores):
    vulnerabilities = dict()
    for cve_id in current_cve_data:
        exploit_found = False
        if cve_scores[cve_id]['components']['Public Exploit Exists']['value'] == 1:
            exploit_found = True
        if exploit_found == True and public_exploit_exists == "Yes":
            vulnerabilities[cve_id] = current_cve_data[cve_id]
        elif exploit_found == False and public_exploit_exists == "No":
            vulnerabilities[cve_id] = current_cve_data[cve_id]
    return vulnerabilities


def get_vulns_filtered_by_exploitation_likeliness(exploitation_likeliness, ms_cve_data):
    # Getting Exploitation is likely vulnerabilities (based on MS data)
    vulnerabilities = dict()
    for cve_id in ms_cve_data:
        latest_rel_expl = ms_cve_data[cve_id]["exploitabilityAssessment"]["latestReleaseExploitability"]["name"]
        if latest_rel_expl == exploitation_likeliness:
            vulnerabilities[cve_id] = ms_cve_data[cve_id]
        older_rel_expl = ms_cve_data[cve_id]["exploitabilityAssessment"]["olderReleaseExploitability"]["name"]
        if older_rel_expl == exploitation_likeliness:
            vulnerabilities[cve_id] = ms_cve_data[cve_id]
    return vulnerabilities


def get_vulns_filtered_by_product(product, cve_data):
    vulnerabilities = dict()
    for cve_id in cve_data:
        if cve_data[cve_id]['vuln_product'] == product:
            vulnerabilities[cve_id] = cve_data[cve_id]
    return vulnerabilities


def get_vulns_filtered_by_type(vuln_type, cve_data):
    vulnerabilities = dict()
    for cve_id in cve_data:
        if cve_data[cve_id]['vuln_type'] == vuln_type:
            vulnerabilities[cve_id] = cve_data[cve_id]
    return vulnerabilities


def get_vulns_filtered_not_in_list(cve_ids, cve_data):
    vulnerabilities = dict()
    for cve_id in cve_data:
        if cve_id not in cve_ids:
            vulnerabilities[cve_id] = cve_data[cve_id]
    return vulnerabilities


### Formating
def get_cve_line(cves):
    # CVE list to string
    cves = list(cves)
    cves.sort()
    cve_line = ", ".join(cves)
    return cve_line


def get_colored_text(color, text, c_type="text", params=None):
    # Make colored HTML text or links
    color_code = "#000000"
    result = ""
    if color == "red":
        color_code = "red"
    if color == "Urgent":
        color_code = "#C70039"
    if color == "Critical":
        color_code = "#FF5733"
    if color == "High":
        color_code = "#E67E22"
    if color == "Medium":
        color_code = "#e6bc0b"
    if color == "Low":
        color_code = "#8d9e63"
    if c_type == "text":
        result = '''<span style="color:''' + color_code + ''';">''' + text + '''</span>'''
    elif c_type == "link":
        result = '''<a style="color:''' + color_code + ''';" href="''' + params['url'] + '''">''' + text + '''</a>'''
    return result


def get_ms_cve_line_html_vss(cve, cve_scores):
    #params = {'url': 'https://portal.msrc.microsoft.com/en-US/security-guidance/advisory/' + cve}
    params = {'url': 'https://vulners.com/cve/' + cve}
    return (get_colored_text(color=cve_scores[cve]['level'],
                             text=cve,
                             c_type="link",
                             params=params))


def get_ms_cve_lines_html_vss(cves, cve_scores):
    # Make colored HTML MS CVE links based on VVS
    cves = list(cves)
    cves.sort()
    cve_html = list()
    for cve_id in cves:
        cve_html.append(get_ms_cve_line_html_vss(cve_id, cve_scores))
    cve_line = ", ".join(cve_html)
    return cve_line


def get_vuln_type_icon_html(type, config):
    vuln_icons_source = config['vuln_icons_source']
    html_img_tag = '<img style="vertical-align: middle; margin-right: 15px; margin-top: 2px; margin-bottom: 2px;" ' \
                   'width="32"  src=" '
    html_img_tag += vuln_icons_source
    html_img_tag += '/' + data_classification_vulnerability_types.vulnerability_type_data[type]['icon'] + '.png">'
    return html_img_tag


def get_vuln_type_html(type, config):
    html_img_tag = get_vuln_type_icon_html(type, config) + type
    return html_img_tag


### Reports
def get_product_based_repot(current_cve_data, min_cve_number, report_config, source, cve_scores):
    processed_cves = set()
    report_txt = ""
    report_html = ""
    all_products = get_vuln_products(current_cve_data)
    for product in all_products:
        product_cves = get_vulns_filtered_by_product(product, current_cve_data)
        number_of_cves = len(product_cves)
        if number_of_cves > min_cve_number:
            report_txt += product + "\n"
            report_html += "<h4>" + product + "</h4>" + "\n"
            report_html += "<ul>" + "\n"
            for type in get_vuln_types(product_cves):
                cves_by_type = get_vulns_filtered_by_type(type, product_cves)
                report_txt += " - " + type + " (" + get_cve_line(cves_by_type.keys()) + ")" + "\n"
                report_html += "<li>" + get_vuln_type_html(type, report_config) + " (" + get_ms_cve_lines_html_vss(
                    cves_by_type.keys(), cve_scores) + ")" + "</li>" + "\n"
                report_html += get_comments_for_cves(source, cves_by_type)["report_html"]
            report_html += "</ul>" + "\n"
            for cve in product_cves.keys():
                processed_cves.add(cve)
    return {"report_txt": report_txt, "report_html": report_html, "processed_cves": processed_cves}


def get_type_based_report(current_cve_data, report_config, source, cve_scores):
    # Make a reports by grouping vulnerabilitites by product and vulnerability vuln_type
    processed_cves = set()
    report_txt = ""
    report_html = ""
    all_types = get_vuln_types(current_cve_data)  # all vulnerability types
    report_dict = dict()
    for vuln_type in all_types:
        report_dict[vuln_type] = dict()
        report_dict[vuln_type]['score'] = 0
        report_dict[vuln_type]['products'] = dict()
        type_cves = get_vulns_filtered_by_type(vuln_type, current_cve_data)
        for product in get_vuln_products(type_cves):
            report_dict[vuln_type]['products'][product] = dict()
            report_dict[vuln_type]['products'][product]['score'] = 0
            report_dict[vuln_type]['products'][product]['cves'] = dict()
            cves_by_product = get_vulns_filtered_by_product(product, type_cves)
            for cve in cves_by_product:
                report_dict[vuln_type]['products'][product]['cves'][cve] = dict()
                report_dict[vuln_type]['products'][product]['cves'][cve]['score'] = cve_scores[cve]
        for cve in type_cves.keys():
            processed_cves.add(cve)
    # Adding max VVS of vulnerabilities as a score for product
    for vuln_type in report_dict:
        for product in report_dict[vuln_type]['products']:
            all_scores = list()
            for cve in report_dict[vuln_type]['products'][product]['cves']:
                all_scores.append(report_dict[vuln_type]['products'][product]['cves'][cve]['score']['value'])
            report_dict[vuln_type]['products'][product]['score'] = max(all_scores)
    # Adding max VVS of products as a score for vulnerability type
    for vuln_type in report_dict:
        all_scores = list()
        for product in report_dict[vuln_type]['products']:
            all_scores.append(report_dict[vuln_type]['products'][product]['score'])
        report_dict[vuln_type]['score'] = max(all_scores)

    def get_cve_for_vuln_type(vuln_type_data):
        all_cves = list()
        for product in vuln_type_data['products']:
            for cve in vuln_type_data['products'][product]['cves']:
                all_cves.append(cve)
        return all_cves

    # Making sorted list of vulnerability types
    vuln_types_dict = dict()
    for vuln_type in report_dict:
        vuln_types_dict[vuln_type] = report_dict[vuln_type]['score']
    sorted_list_of_vulnerability_types = functions_tools.get_sorted_list_from_weighted_dict(vuln_types_dict)
    for vuln_type in sorted_list_of_vulnerability_types:
        report_txt += vuln_type + "\n"
        report_html += "<h4>" + get_vuln_type_html(vuln_type, report_config) + " (" + str(
            len(get_cve_for_vuln_type(report_dict[vuln_type]))) + ")</h4>" + "\n"
        report_html += "<ul>" + "\n"
        # Making sorted list of products
        product_dict = dict()
        for product in report_dict[vuln_type]['products']:
            product_dict[product] = report_dict[vuln_type]['products'][product]['score']
        sorted_list_of_products = functions_tools.get_sorted_list_from_weighted_dict(product_dict)
        for product in sorted_list_of_products:
            cves = report_dict[vuln_type]['products'][product]['cves'].keys()
            cves = list(cves)
            cves.sort()
            report_txt += " - " + product + " (" + get_cve_line(cves) + ")" + "\n"
            report_html += "<li>" + product + " (" + get_ms_cve_lines_html_vss(cves, cve_scores) + ")" + "</li>" + "\n"
            report_html += get_comments_for_cves(source, cves)["report_html"]
        report_html += "</ul>" + "\n"

    return {"report_txt": report_txt, "report_html": report_html, "report_dict": report_dict,
            "processed_cves": processed_cves}


def get_components_list_sorted(cve_scores):
    cve_id = list(cve_scores.keys())[0]
    component_dict = dict()
    for component in cve_scores[cve_id]['components']:
        component_dict[component] = cve_scores[cve_id]['components'][component]['weight']
    components = functions_tools.get_sorted_list_from_weighted_dict(component_dict)
    # for component in components:
    #     print(component + ";" + str(component_dict[component]))
    return components


def get_statistics(cve_scores):
    statistics = {
        "Urgent": set(),
        "Critical": set(),
        "High": set(),
        "Medium": set(),
        "Low": set(),
        "All vulnerabilities": set()
    }
    for cve in cve_scores:
        statistics[cve_scores[cve]['level']].add(cve)
        statistics["All vulnerabilities"].add(cve)
    return statistics


def get_vulristics_score_vulner_block(cve_scores, combined_cve_data_all, config, components, source, cve, n):
    report_html = ""
    report_html += "<p>" + get_colored_text("red", str(n) + ". ") + get_vuln_type_icon_html(
        combined_cve_data_all[cve]['vuln_type'], config) + \
                   " <b>" + str(combined_cve_data_all[cve]['vuln_type']) + \
                   "</b> - " + str(combined_cve_data_all[cve]['vuln_product']) + \
                   " (" + get_ms_cve_line_html_vss(cve, cve_scores) + ")" + \
                   " - " + get_colored_text(cve_scores[cve]['level'], cve_scores[cve]['level'] + " [" + str(
        int(cve_scores[cve]['value'] * 1000)) + "] ") + \
                   "</br>"
    report_html += "<p><b>Description:</b> " + combined_cve_data_all[cve]['description'] + "</p>"

    report_html += "<table class=\"vvs_table\"><tr class=\"vvs_table\"><th class=\"vvs_table\">component</th><th class=\"vvs_table\">value</th><th class=\"vvs_table\">weight</th><th class=\"vvs_table\">comment</th></tr>"
    for component in components:
        report_html += "<tr class=\"vvs_table\">" + \
                       "<td class=\"vvs_table\"><nowrap>" + component + "</nowrap></td>" + \
                       "<td class=\"vvs_table\">" + get_colored_text(cve_scores[cve]['components'][component]['level'], str(
            cve_scores[cve]['components'][component]['value'])) + "</td>" + \
                       "<td class=\"vvs_table\">" + str(cve_scores[cve]['components'][component]['weight']) + "</td>" + \
                       "<td class=\"vvs_table\">" + get_colored_text(cve_scores[cve]['components'][component]['level'], str(
            cve_scores[cve]['components'][component]['comment'])) + "</td>" + \
                       "</tr>"
    report_html += "</table>"
    report_html += get_comments_for_cves(source, [cve])['report_html']
    report_html += "</p>\n"
    return report_html


def get_vvs_statistics_report(cve_scores):
    report_txt = ""
    report_html = ""

    statistics = get_statistics(cve_scores)

    cve_score_dict = dict()
    for cve in cve_scores:
        cve_score_dict[cve] = int(cve_scores[cve]['value'] * 1000)

    criticalities = ["Urgent", "Critical", "High", "Medium", "Low"]
    report_html += "<ul>"
    report_html += "<li>" + "All vulnerabilities" + ': ' + str(len(statistics["All vulnerabilities"])) + "</li>"
    for criticality in criticalities:
        report_html += "<li>" + get_colored_text(criticality, criticality) + ': ' + str(
            len(statistics[criticality])) + "</li>"
    report_html += "</ul>"

    return {"report_txt": report_txt, "report_html": report_html}


def get_vulristics_score_report(combined_cve_data_all, cve_scores, config, source):
    report_txt = ""
    report_html = ""

    statistics = get_statistics(cve_scores)

    cve_score_dict = dict()
    for cve in cve_scores:
        cve_score_dict[cve] = int(cve_scores[cve]['value'] * 1000)
    sorted_cves = functions_tools.get_sorted_list_from_weighted_dict(cve_score_dict)

    criticalities = ["Urgent", "Critical", "High", "Medium", "Low"]
    components = get_components_list_sorted(cve_scores)

    n = 1
    for criticality in criticalities:
        report_html += "<h4>" + criticality + " (" + str(len(statistics[criticality])) + ")</h4>"
        for cve in sorted_cves:
            if cve in statistics[criticality] and cve in combined_cve_data_all:
                report_html += get_vulristics_score_vulner_block(cve_scores, combined_cve_data_all, config, components,
                                                                 source, cve, n)
                n += 1

    return {"report_txt": report_txt, "report_html": report_html}


def get_products_report(combined_cve_data_all, cve_scores, config, source):
    report_txt = ""
    report_html = ""
    criticalities = ["Urgent", "Critical", "High", "Medium", "Low"]
    product_data = dict()
    for cve in combined_cve_data_all:
        product = combined_cve_data_all[cve]['vuln_product']
        value = cve_scores[cve]['components']['Vulnerable Product is Common']['value']
        comment = cve_scores[cve]['components']['Vulnerable Product is Common']['comment']
        cve_level = cve_scores[cve]['level']
        if not product in product_data:
            product_data[product] = dict()
            product_data[product]['cves'] = dict()
            product_data[product]['value'] = value
            product_data[product]['comment'] = comment
            for crit in criticalities:
                product_data[product]['cves'][crit] = list()
        product_data[product]['cves'][cve_level].append(cve)
    print(product_data)
    return {"report_txt": report_txt, "report_html": report_html}

def get_basic_severity_statistics_report(combined_cve_data_all):
    report_txt = ""
    report_html = ""

    all_vulnerabilities = set()
    for vulnerability in combined_cve_data_all:
        all_vulnerabilities.add(vulnerability)

    critical_vulnerability = set()
    high_vulnerability = set()
    medium_vulnerability = set()
    low_vulnerability = set()

    for vulnerability in combined_cve_data_all:
        cvss_base_score = combined_cve_data_all[vulnerability]['cvss_base_score']
        basic_severity = functions_tools.get_rating_from_cvss_base_score(cvss_base_score)
        if basic_severity == "Critical":
            critical_vulnerability.add(vulnerability)
        elif basic_severity == "High":
            high_vulnerability.add(vulnerability)
        elif basic_severity == "Medium":
            medium_vulnerability.add(vulnerability)
        elif basic_severity == "low":
            low_vulnerability.add(vulnerability)

    report_txt += "All vulnerabilities: " + str(len(all_vulnerabilities)) + "\n"
    report_txt += "Critical: " + str(len(critical_vulnerability)) + "\n"
    report_txt += "High: " + str(len(high_vulnerability)) + "\n"
    report_txt += "Medium: " + str(len(medium_vulnerability)) + "\n"
    report_txt += "Low: " + str(len(low_vulnerability)) + "\n"
    report_html += "<ul>" + "\n"
    report_html += "<li>" + "All vulnerabilities: " + str(len(all_vulnerabilities)) + "</li>" + "\n"
    report_html += "<li>" + "Critical: " + str(len(critical_vulnerability)) + "</li>" + "\n"
    report_html += "<li>" + "High: " + str(len(high_vulnerability)) + "</li>" + "\n"
    report_html += "<li>" + "Medium: " + str(len(medium_vulnerability)) + "</li>" + "\n"
    report_html += "<li>" + "Low: " + str(len(low_vulnerability)) + "</li>" + "\n"
    report_html += "</ul>" + "\n"

    return {"report_txt": report_txt, "report_html": report_html}


def get_comments_for_cves(source, processed_cves):
    report_html = ""
    if 'comments' in source:
        comments = source['comments']
        for comment_id in comments:
            for line in comments[comment_id].split("\n"):
                print_line = False
                for cve in processed_cves:
                    if cve in line:
                        print_line = True
                if print_line:
                    for cve in processed_cves:
                        line = re.sub(cve, "<b>" + cve + "</b>", line)
                    report_html += "<p>" + comment_id + ": " + line + "</p>" + "\n"

    return {"report_html": report_html}


def make_html_vulnerability_report_for_report_config(cve_related_data, cve_scores, report_config, profile_data):
    html_content = "<center><img class=\"logo\" src=\"" + report_config['vuln_icons_source'] + "/vulristics.png\"></center>"
    combined_cve_data = cve_related_data['combined_cve_data_all']

    if report_config['ignore_comments']:
        profile_data['comments'] = {}

    f = open("reports/template.html", "r")
    template = f.read()
    f.close()

    now = datetime.now()
    html_content += "<p><b>Report name:</b> " + profile_data['report_name'] + "</br>"
    html_content += "<b>Generated:</b> " + now.strftime("%Y-%m-%d %H:%M:%S") + "</p>"


    report_data = get_basic_severity_statistics_report(combined_cve_data)
    name = "Basic Vulnerability Scores"
    print("== " + name + " ==")
    basic_score_html_content = "<b>" + name + "</b>" + "\n"
    print(report_data['report_txt'])
    basic_score_html_content += report_data['report_html']

    report_data = get_vvs_statistics_report(cve_scores)
    name = "Vulristics Vulnerability Scores"
    print("== " + name + " ==")
    vulristics_score_html_content = "<b>" + name + "</b>" + "\n"
    print(report_data['report_txt'])
    vulristics_score_html_content += report_data['report_html']

    html_content += "<div class=\"row\"> <div class=\"column\">" + vulristics_score_html_content + "</div>" + \
                    "<div class=\"column\">" +  basic_score_html_content + "</div> </div>"
    # ^^^  - two columns with VVS and CVSS

    # list of all products

    report_data = get_products_report(combined_cve_data, cve_scores, report_config, profile_data)
    name = "Products"
    print("== " + name + " ==")
    html_content += "<b>" + name + "</b>" + "\n"
    print(report_data['report_txt'])
    html_content += report_data['report_html']
    html_content += "</br>"

    report_data = get_vulristics_score_report(combined_cve_data, cve_scores, report_config, profile_data)
    name = "Vulnerabilities"
    print("== " + name + " ==")
    html_content += "<b>" + name + "</b>" + "\n"
    print(report_data['report_txt'])
    html_content += report_data['report_html']


    current_cve_data = combined_cve_data
    exploited_cves = get_vulns_filtered_by_wild_exploited("Yes", current_cve_data, cve_scores)
    report_data = get_type_based_report(exploited_cves, report_config, profile_data, cve_scores)
    name = "Exploitation in the wild detected"
    print("== " + name + " (" + str(len(report_data['processed_cves'])) + ") ==")
    html_content += "<h3>" + name + " (" + str(len(report_data['processed_cves'])) + ")</h3>" + "\n"
    print(report_data['report_txt'])
    html_content += report_data['report_html']
    # html_content += get_comments_for_cves(source, report_data['processed_cves'])["report_html"]
    current_cve_data = get_vulns_filtered_not_in_list(report_data['processed_cves'], current_cve_data)

    exploited_cves = get_vulns_filtered_by_public_exploit_exists("Yes", current_cve_data, cve_scores)
    report_data = get_type_based_report(exploited_cves, report_config, profile_data, cve_scores)
    name = "Public exploit exists, but exploitation in the wild is NOT detected"
    print("== " + name + " (" + str(len(report_data['processed_cves'])) + ") ==")
    html_content += "<h3>" + name + " (" + str(len(report_data['processed_cves'])) + ")</h3>" + "\n"
    print(report_data['report_txt'])
    html_content += report_data['report_html']
    # html_content += get_comments_for_cves(source, report_data['processed_cves'])["report_html"]
    current_cve_data = get_vulns_filtered_not_in_list(report_data['processed_cves'], current_cve_data)

    ####### Commented legacy blocks from the reports
    # exploitation_more_likely = get_vulns_filtered_by_exploitation_likeliness("Exploitation More Likely",
    #                                                                          current_cve_data, cve_scores)
    # report_data = get_type_based_repot(exploitation_more_likely, report_config, source)
    # name = "Exploitation more likely"
    # print("== " + name + " (" + str(len(report_data['processed_cves'])) + ") ==")
    # html_content += "<h3>" + name + " (" + str(len(report_data['processed_cves'])) + ")</h3>" + "\n"
    # print(report_data['report_txt'])
    # html_content += report_data['report_html']
    # # html_content += get_comments_for_cves(source, report_data['processed_cves'])["report_html"]
    # current_cve_data = get_vulns_filtered_not_in_list(report_data['processed_cves'], current_cve_data)

    # report_data = get_product_based_repot(current_cve_data, min_cve_number=5, report_config=report_config,
    #                                       source=source, cve_scores)
    # name = "Other Product based "
    # print("== " + name + " (" + str(len(report_data['processed_cves'])) + ") ==")
    # html_content += "<h3>" + name + " (" + str(len(report_data['processed_cves'])) + ")</h3>" + "\n"
    # print(report_data['report_txt'])
    # html_content += report_data['report_html']
    # # html_content += get_comments_for_cves(source, report_data['processed_cves'])["report_html"]
    # current_cve_data = get_vulns_filtered_not_in_list(report_data['processed_cves'], current_cve_data)

    report_data = get_type_based_report(current_cve_data, report_config, profile_data, cve_scores)
    name = "Other Vulnerabilities"
    print("== " + name + " (" + str(len(report_data['processed_cves'])) + ") ==")
    html_content += "<h3>" + name + " (" + str(len(report_data['processed_cves'])) + ")</h3>" + "\n"
    print(report_data['report_txt'])
    html_content += report_data['report_html']
    # html_content += get_comments_for_cves(source, report_data['processed_cves'])["report_html"]
    current_cve_data = get_vulns_filtered_not_in_list(report_data['processed_cves'], current_cve_data)

    html_content = re.sub("##Content##", html_content, template)

    f = open("reports/" + profile_data['file_name_prefix'] + "_" + report_config['file_name_suffix'] + ".html", "w",
             encoding="utf-8")
    f.write(html_content)
    f.close()


def add_ms_cve_data(enabled_data_sources, all_cves, cve_data_all, cves_to_exclude, rewrite_flag):
    if "ms" in enabled_data_sources:
        functions_tools.print_debug_message("Collecting MS CVE data...")
        ms_cve_data_all = dict()
        for cve_id in all_cves:
            ms_cve_data = functions_source_ms_cve.get_ms_cve_data(cve_id, rewrite_flag)
            if 'cveTitle' in ms_cve_data['main']:
                if ms_cve_data['main']['cveTitle'] == "RETRACTED":
                    functions_tools.print_debug_message("Adding RETRACTED " + cve_id + " to cves_to_exclude")
                    cves_to_exclude.add(cve_id)
                elif ms_cve_data['not_found_error']:
                    functions_tools.print_debug_message("Adding NOT FOUND " + cve_id + " to cves_to_exclude")
                    cves_to_exclude.add(cve_id)
                else:
                    ms_cve_data_all[cve_id] = ms_cve_data
        cve_data_all['ms_cve_data_all'] = ms_cve_data_all
    return cve_data_all, cves_to_exclude


def add_nvd_cve_data(enabled_data_sources, all_cves, cve_data_all, rewrite_flag):
    if "nvd" in enabled_data_sources:
        functions_tools.print_debug_message("Collecting NVD CVE data...")
        nvd_cve_data_all = dict()
        for cve_id in all_cves:
            nvd_cve_data = functions_source_nvd_cve.get_nvd_cve_data(cve_id, rewrite_flag)
            nvd_cve_data_all[cve_id] = nvd_cve_data
        cve_data_all['nvd_cve_data_all'] = nvd_cve_data_all
    return cve_data_all


def add_attackerkb_cve_data(enabled_data_sources, all_cves, cve_data_all, rewrite_flag):
    if "attackerkb" in enabled_data_sources:
        functions_tools.print_debug_message("Collecting AttackerKB CVE data...")
        attackerkb_cve_data_all = dict()
        for cve_id in all_cves:
            attackerkb_cve_data = functions_source_attackerkb_cve.get_attackerkb_cve_data(cve_id, rewrite_flag)
            attackerkb_cve_data_all[cve_id] = attackerkb_cve_data
        cve_data_all['attackerkb_cve_data_all'] = attackerkb_cve_data_all
    return cve_data_all


def add_vulners_cve_data(enabled_data_sources, all_cves, cve_data_all, rewrite_flag):
    if "vulners" in enabled_data_sources:
        functions_tools.print_debug_message("Collecting Vulners CVE data...")
        vulners_cve_data_all = dict()
        if credentials.vulners_key != "":  # If we  have Vulners API key
            for cve_id in all_cves:
                vulners_cve_data = functions_source_vulners.get_vulners_data(cve_id, rewrite_flag)
                vulners_cve_data_all[cve_id] = vulners_cve_data
        cve_data_all['vulners_cve_data_all'] = vulners_cve_data_all
    return cve_data_all


def add_combined_cve_data_vuln_product(cve_data_all, cve_id):
    # Combining the data about the Product
    cve_data_all['combined_cve_data_all'][cve_id]['vuln_product'] = ""
    cve_data_all['combined_cve_data_all'][cve_id]['vuln_product_detection_comment'] = ""
    # Microsoft has the most accurate data, so I give it the first priority
    if cve_data_all['combined_cve_data_all'][cve_id]['vuln_product'] == "":
        if 'ms_cve_data_all' in cve_data_all:
            if cve_id in cve_data_all['ms_cve_data_all']:
                if 'vuln_product' in cve_data_all['ms_cve_data_all'][cve_id]:
                    cve_data_all['combined_cve_data_all'][cve_id]['vuln_product'] = \
                        cve_data_all['ms_cve_data_all'][cve_id]['vuln_product']
                    cve_data_all['combined_cve_data_all'][cve_id]['vuln_product_detection_comment'] = \
                        "Based on Microsoft title"
    # If there is no data in MS, let's get it from NVD description
    if cve_data_all['combined_cve_data_all'][cve_id]['vuln_product'] == "":
        if 'nvd_cve_data_all' in cve_data_all:
            if cve_id in cve_data_all['nvd_cve_data_all']:
                if 'vuln_product' in cve_data_all['nvd_cve_data_all'][cve_id]:
                    cve_data_all['combined_cve_data_all'][cve_id]['vuln_product'] = \
                        cve_data_all['nvd_cve_data_all'][cve_id]['vuln_product']
                    cve_data_all['combined_cve_data_all'][cve_id]['vuln_product_detection_comment'] = \
                        "Based on NVD description"
    # If there is no data in NVD, let's get it from Vulners description
    if cve_data_all['combined_cve_data_all'][cve_id]['vuln_product'] == "":
        if 'vulners_cve_data_all' in cve_data_all:
            if cve_id in cve_data_all['vulners_cve_data_all']:
                if 'vuln_product' in cve_data_all['vulners_cve_data_all'][cve_id]:
                    cve_data_all['combined_cve_data_all'][cve_id]['vuln_product'] = \
                        cve_data_all['vulners_cve_data_all'][cve_id]['vuln_product']
                    cve_data_all['combined_cve_data_all'][cve_id]['vuln_product_detection_comment'] = \
                        "Based on Vulners description"
    # If it's still empty, then set it to "Unknown Product"
    if cve_data_all['combined_cve_data_all'][cve_id]['vuln_product'] == "":
        cve_data_all['combined_cve_data_all'][cve_id]['vuln_product'] = "Unknown Product"
        cve_data_all['combined_cve_data_all'][cve_id]['vuln_product_detection_comment'] = "Detection methods failed"
    return cve_data_all


def add_combined_cve_data_vuln_type(cve_data_all, cve_id):
    # Combining the data about the Vulnerability Type
    cve_data_all['combined_cve_data_all'][cve_id]['vuln_type'] = ""
    cve_data_all['combined_cve_data_all'][cve_id]['vuln_type_detection_comment'] = ""
    # Microsoft has the most accurate data, so I give it the first priority
    if cve_data_all['combined_cve_data_all'][cve_id]['vuln_type'] == "":
        if 'ms_cve_data_all' in cve_data_all:
            if cve_id in cve_data_all['ms_cve_data_all']:
                if 'vuln_type' in cve_data_all['ms_cve_data_all'][cve_id]:
                    cve_data_all['combined_cve_data_all'][cve_id]['vuln_type'] = \
                        cve_data_all['ms_cve_data_all'][cve_id]['vuln_type']
                    cve_data_all['combined_cve_data_all'][cve_id]['vuln_type_detection_comment'] = \
                        "Based on Microsoft title"
    # If there is no data in MS, let's get it from NVD description
    if cve_data_all['combined_cve_data_all'][cve_id]['vuln_type'] == "":
        if 'nvd_cve_data_all' in cve_data_all:
            if cve_id in cve_data_all['nvd_cve_data_all']:
                if 'vuln_type' in cve_data_all['nvd_cve_data_all'][cve_id]:
                    cve_data_all['combined_cve_data_all'][cve_id]['vuln_type'] = \
                        cve_data_all['nvd_cve_data_all'][cve_id]['vuln_type']
                    cve_data_all['combined_cve_data_all'][cve_id]['vuln_type_detection_comment'] = \
                        "Based on NVD description"
    # If there is no data in VND, let's get it from Vulners description
    if cve_data_all['combined_cve_data_all'][cve_id]['vuln_type'] == "":
        if 'vulners_cve_data_all' in cve_data_all:
            if cve_id in cve_data_all['vulners_cve_data_all']:
                if 'vuln_type' in cve_data_all['vulners_cve_data_all'][cve_id]:
                    cve_data_all['combined_cve_data_all'][cve_id]['vuln_type'] = \
                        cve_data_all['vulners_cve_data_all'][cve_id]['vuln_type']
                    cve_data_all['combined_cve_data_all'][cve_id]['vuln_type_detection_comment'] = \
                        "Based on Vulners description"
    # If it's still empty, then set it to  "Unknown type"
    if cve_data_all['combined_cve_data_all'][cve_id]['vuln_type'] == "":
        cve_data_all['combined_cve_data_all'][cve_id]['vuln_type'] = "Unknown Vulnerability Type"
        cve_data_all['combined_cve_data_all'][cve_id]['vuln_type_detection_comment'] = "Detection methods failed"
    return cve_data_all


def add_combined_cve_data_basic_severity(cve_data_all, cve_id):
    # Combining the data about the Basic Severity
    cve_data_all['combined_cve_data_all'][cve_id]['basic_severity'] = ""
    cve_data_all['combined_cve_data_all'][cve_id]['basic_severity_detection_comment'] = ""
    # Microsoft has the most accurate data, so I give it the first priority
    if cve_data_all['combined_cve_data_all'][cve_id]['basic_severity'] == "":
        if 'ms_cve_data_all' in cve_data_all:
            if cve_id in cve_data_all['ms_cve_data_all']:
                if 'basic_severity' in cve_data_all['ms_cve_data_all'][cve_id]:
                    cve_data_all['combined_cve_data_all'][cve_id]['basic_severity'] = \
                        cve_data_all['ms_cve_data_all'][cve_id]['basic_severity']
                    cve_data_all['combined_cve_data_all'][cve_id]['basic_severity_detection_comment'] = \
                        "Based on Microsoft title"
    # If there is no data in MS, let's get it from NVD description
    if cve_data_all['combined_cve_data_all'][cve_id]['basic_severity'] == "":
        if 'nvd_cve_data_all' in cve_data_all:
            if cve_id in cve_data_all['nvd_cve_data_all']:
                if 'basic_severity' in cve_data_all['nvd_cve_data_all'][cve_id]:
                    cve_data_all['combined_cve_data_all'][cve_id]['basic_severity'] = \
                        cve_data_all['nvd_cve_data_all'][cve_id]['basic_severity']
                    cve_data_all['combined_cve_data_all'][cve_id]['basic_severity_detection_comment'] = \
                        "Based on NVD description"
    # If there is no data in NVD, let's get it from Vulners description
    if cve_data_all['combined_cve_data_all'][cve_id]['basic_severity'] == "":
        if 'vulners_cve_data_all' in cve_data_all:
            if cve_id in cve_data_all['vulners_cve_data_all']:
                if 'basic_severity' in cve_data_all['vulners_cve_data_all'][cve_id]:
                    cve_data_all['combined_cve_data_all'][cve_id]['basic_severity'] = \
                        cve_data_all['vulners_cve_data_all'][cve_id]['basic_severity']
                    cve_data_all['combined_cve_data_all'][cve_id]['basic_severity_detection_comment'] = \
                        "Based on Vulners description"
    # If it's still empty, then set it to  "Unknown type"
    if cve_data_all['combined_cve_data_all'][cve_id]['basic_severity'] == "":
        cve_data_all['combined_cve_data_all'][cve_id]['basic_severity'] = "Unknown Basic Severity"
        cve_data_all['combined_cve_data_all'][cve_id]['basic_severity_detection_comment'] = "Detection methods failed"
    return cve_data_all


def add_combined_cve_data_cvss_base_score(cve_data_all, cve_id):
    # Combining the data about the CVSS Base Score
    cve_data_all['combined_cve_data_all'][cve_id]['cvss_base_score'] = ""
    cve_data_all['combined_cve_data_all'][cve_id]['cvss_base_score_detection_comment'] = ""
    # Microsoft has the most accurate data, so I give it the first priority
    if cve_data_all['combined_cve_data_all'][cve_id]['cvss_base_score'] == "":
        if 'ms_cve_data_all' in cve_data_all:
            if cve_id in cve_data_all['ms_cve_data_all']:
                if 'cvss_base_score' in cve_data_all['ms_cve_data_all'][cve_id]:
                    cve_data_all['combined_cve_data_all'][cve_id]['cvss_base_score'] = \
                        cve_data_all['ms_cve_data_all'][cve_id]['cvss_base_score']
                    cve_data_all['combined_cve_data_all'][cve_id]['cvss_base_score_detection_comment'] = \
                        "Based on Microsoft data"
    # If there is no data in MS, let's get it from NVD description
    if cve_data_all['combined_cve_data_all'][cve_id]['cvss_base_score'] == "":
        if 'nvd_cve_data_all' in cve_data_all:
            if cve_id in cve_data_all['nvd_cve_data_all']:
                if 'cvss_base_score' in cve_data_all['nvd_cve_data_all'][cve_id]:
                    cve_data_all['combined_cve_data_all'][cve_id]['cvss_base_score'] = \
                        cve_data_all['nvd_cve_data_all'][cve_id]['cvss_base_score']
                    cve_data_all['combined_cve_data_all'][cve_id]['cvss_base_score_detection_comment'] = \
                        "Based on NVD data"
    # If there is no data in NVD, let's get it from Vulners description
    if cve_data_all['combined_cve_data_all'][cve_id]['cvss_base_score'] == "":
        if 'vulners_cve_data_all' in cve_data_all:
            if cve_id in cve_data_all['vulners_cve_data_all']:
                if 'cvss_base_score' in cve_data_all['vulners_cve_data_all'][cve_id]:
                    cve_data_all['combined_cve_data_all'][cve_id]['cvss_base_score'] = \
                        cve_data_all['vulners_cve_data_all'][cve_id]['cvss_base_score']
                    cve_data_all['combined_cve_data_all'][cve_id]['cvss_base_score_detection_comment'] = \
                        "Based on Vulners data"
    # If it's still empty, then set it to  "Unknown type"
    if cve_data_all['combined_cve_data_all'][cve_id]['cvss_base_score'] == "":
        cve_data_all['combined_cve_data_all'][cve_id]['cvss_base_score'] = "Unknown CVSS Base Score"
        cve_data_all['combined_cve_data_all'][cve_id]['cvss_base_score_detection_comment'] = "Detection methods failed"
    return cve_data_all


def add_combined_cve_data_description(cve_data_all, cve_id):
    # Combining the data about Vulnerability Description
    cve_data_all['combined_cve_data_all'][cve_id]['description'] = ""
    cve_data_all['combined_cve_data_all'][cve_id]['description_tags'] = ""
    cve_data_all['combined_cve_data_all'][cve_id]['description_detection_comment'] = ""
    # I take it only from NVD
    if cve_data_all['combined_cve_data_all'][cve_id]['description'] == "":
        if 'nvd_cve_data_all' in cve_data_all:
            if cve_id in cve_data_all['nvd_cve_data_all']:
                if 'description' in cve_data_all['nvd_cve_data_all'][cve_id]:
                    cve_data_all['combined_cve_data_all'][cve_id]['description'] = \
                        cve_data_all['nvd_cve_data_all'][cve_id]['description']
                    # I should use description_tags (ranges) to mark products and vuln types in the description
                    cve_data_all['combined_cve_data_all'][cve_id]['description_tags'] = \
                        cve_data_all['nvd_cve_data_all'][cve_id]['description_tags']
                    cve_data_all['combined_cve_data_all'][cve_id]['description_detection_comment'] = \
                        "Based on NVD data"
    # Or Vulners
    if cve_data_all['combined_cve_data_all'][cve_id]['description'] == "":
        if 'vulners_cve_data_all' in cve_data_all:
            if cve_id in cve_data_all['vulners_cve_data_all']:
                if 'description' in cve_data_all['vulners_cve_data_all'][cve_id]:
                    cve_data_all['combined_cve_data_all'][cve_id]['description'] = \
                        cve_data_all['vulners_cve_data_all'][cve_id]['description']
                    # I should use description_tags (ranges) to mark products and vuln types in the description
                    cve_data_all['combined_cve_data_all'][cve_id]['description_tags'] = \
                        cve_data_all['vulners_cve_data_all'][cve_id]['description_tags']
                    cve_data_all['combined_cve_data_all'][cve_id]['description_detection_comment'] = \
                        "Based on Vulners data"
    return cve_data_all


def add_combined_cve_data(all_cves, cve_data_all):
    cve_data_all['combined_cve_data_all'] = dict()
    for cve_id in all_cves:
        cve_data_all['combined_cve_data_all'][cve_id] = dict()
        cve_data_all = add_combined_cve_data_vuln_product(cve_data_all, cve_id)
        cve_data_all = add_combined_cve_data_vuln_type(cve_data_all, cve_id)
        cve_data_all = add_combined_cve_data_basic_severity(cve_data_all, cve_id)
        cve_data_all = add_combined_cve_data_cvss_base_score(cve_data_all, cve_id)
        cve_data_all = add_combined_cve_data_description(cve_data_all, cve_id)
    return cve_data_all


def collect_cve_related_data(enabled_data_sources, all_cves, cves_to_exclude, rewrite_flag):
    """
    Collecting vulnerability data from the supported sources and
                                                        combining basic vulnerability data in combined_cve_data_all
    :param all_cves:
    :param rewrite_flag:
    :return:
    """

    # Collecting vulnerability data from the supported sources
    functions_tools.print_debug_message("Counting CVE scores...")
    cve_data_all = dict()
    cve_data_all, cves_to_exclude = add_ms_cve_data(enabled_data_sources, all_cves, cve_data_all,
                                                    cves_to_exclude, rewrite_flag)
    cve_data_all = add_nvd_cve_data(enabled_data_sources, all_cves, cve_data_all, rewrite_flag)
    cve_data_all = add_attackerkb_cve_data(enabled_data_sources, all_cves, cve_data_all, rewrite_flag)
    cve_data_all = add_vulners_cve_data(enabled_data_sources, all_cves, cve_data_all, rewrite_flag)
    cve_data_all = add_combined_cve_data(all_cves, cve_data_all)
    return cve_data_all, cves_to_exclude


def get_profile(file_path):
    functions_tools.print_debug_message("Reading existing Patch Tuesday profile...")
    f = open(file_path, "r")
    profile = json.loads(f.read())
    f.close()
    return profile


def get_cves_to_exclude(profile, source_id):
    cves_to_exclude = set()
    if 'cves_exclude_text' in profile[source_id]:
        cves_exclude_text = profile[source_id]['cves_exclude_text']
        for line in cves_exclude_text.split("\n"):
            if re.findall("^CVE", line.upper()):
                cves_to_exclude.add(line.upper())
    functions_tools.print_debug_message("Exclude CVEs: " + str(len(cves_to_exclude)))
    return cves_to_exclude


def get_all_cves(profile, source_id, cves_to_exclude):
    cves_text = profile[source_id]['cves_text']
    all_cves = set()
    for line in cves_text.split("\n"):
        if re.findall("^CVE", line.upper()):
            if line.upper() not in cves_to_exclude:
                all_cves.add(line.upper())
    functions_tools.print_debug_message("All CVEs: " + str(len(all_cves)))
    return all_cves


def print_unclassified_products_templates(cve_scores, cve_related_data):
    unclassified_products = set()
    for cve in cve_scores:
        if cve_scores[cve]['components']['Vulnerable Product is Common']['comment'] == "Unclassified product":
            unclassified_products.add(cve_related_data['combined_cve_data_all'][cve]['vuln_product'])
    unclassified_products = list(unclassified_products)
    unclassified_products.sort()
    if unclassified_products != list():
        functions_tools.print_debug_message("Add this to data_classification_products.py")
        for product in unclassified_products:
            print('''    "''' + product + '''": {
            "prevalence": 0,
            "description": "",
            "additional_detection_strings": []
        },''')


def make_html_vulnerability_reports_for_all_report_configs(profile, source_id, cve_related_data, cve_scores):
    functions_tools.print_debug_message("Making vulnerability reports for each reports config...")
    for report_config_name in data_report_configs.patch_tuesday_report_configs:
        functions_tools.print_debug_message("Report config: " + report_config_name)
        report_config = data_report_configs.patch_tuesday_report_configs[report_config_name]
        make_html_vulnerability_report_for_report_config(cve_related_data=cve_related_data,
                                                         cve_scores=cve_scores,
                                                         report_config=report_config,
                                                         profile_data=profile[source_id])


def get_eanbled_data_sources(profile, source_id):
    all_data_sources = ['ms', 'nvd', 'vulners', 'attackerkb']
    if 'data_sources' in profile[source_id]:
        enabled_data_sources = profile[source_id]['data_sources']
    else:
        enabled_data_sources = all_data_sources
    return enabled_data_sources


def make_vulnerability_report_for_profile(profile_file_path, rewrite_flag):
    profile = get_profile(profile_file_path)
    source_id = list(profile.keys())[0]
    cves_to_exclude = get_cves_to_exclude(profile, source_id)
    all_cves = get_all_cves(profile, source_id, cves_to_exclude)

    enabled_data_sources = get_eanbled_data_sources(profile, source_id)
    cve_related_data, cves_to_exclude = collect_cve_related_data(enabled_data_sources, all_cves,
                                                                 cves_to_exclude, rewrite_flag)

    cve_scores = functions_score.get_cve_scores(all_cves, cve_related_data, profile[source_id])

    print_unclassified_products_templates(cve_scores, cve_related_data)
    make_html_vulnerability_reports_for_all_report_configs(profile, source_id, cve_related_data, cve_scores)
