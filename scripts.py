import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
import time


con = con = sqlite3.connect(
    "./bce.db")

# PRE-LOADING QUESTION 1

df_juridicform = pd.read_sql('SELECT * FROM enterprise', con)
df_juridicformcodes = pd.read_sql(
    'SELECT Code, Description FROM code WHERE Category="JuridicalForm" AND Language="FR"', con)

df_juridicform_extend = pd.merge(
    df_juridicform, df_juridicformcodes, how='left', left_on='JuridicalForm', right_on='Code')

first_question = df_juridicform_extend.groupby(
    ['JuridicalForm', 'Description'], as_index=False).agg({'EnterpriseNumber': 'count'})
first_question['Percentage'] = first_question['EnterpriseNumber'] / \
    sum(first_question['EnterpriseNumber']) * 100
first_question.sort_values('Percentage', ascending=False, inplace=True)

first_question_1 = first_question[:6]
data = [{'JuridicalForm': 000, 'Description': 'Autres', 'EnterpriseNumber': first_question['EnterpriseNumber']
         [6:].sum(), 'Percentage':first_question['Percentage'][6:].sum()}]
first_question_2 = pd.DataFrame(data)

first_question_last = pd.concat([first_question_1, first_question_2])


# GENERAL CUSTOMIZATION



# CSS to hide the index of the tables
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """


st.set_page_config(layout="centered", page_title="Database BeCode excercices", initial_sidebar_state='auto', page_icon="chart_with_upwards_trend")

st.markdown(hide_table_row_index, unsafe_allow_html=True)
st.title("**Belgian Companies Info Dashboard**")

# Definition of tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
    ['Juridical Form', 'Status', 'Type Of Company','Avg Age Per Sectors','Map','Sectors','Compagnies Language','Creds'])

# Question 1
with tab1:
    
    st.header("Juridical Form Of Companies")

    st.subheader("Top 6 juridical forms")
    fig1, ax1 = plt.subplots()
    ax1.pie(first_question_last['Percentage'], labels=first_question_last['Description'], autopct='%1.1f%%',
            shadow=False, startangle=30)
    ax1.axis('equal')
    st.pyplot(fig1, transparent=True)

    st.text("Detailed information:")
    st.table(first_question_last)

# Question 2
with tab2:
    st.header("Status Of Companies")

    df_status = pd.read_sql(
            "SELECT Status, Count(Status) FROM enterprise", con)
    fig2, ax2 = plt.subplots()
    ax2.pie(df_status['Count(Status)'], labels=df_status['Status'], autopct='%1.1f%%',
            shadow=False)
    ax2.axis('equal')
    st.pyplot(fig2, transparent=True)
    st.caption("AC : Active")

    st.table(df_status)

# Question 3
with tab3:
    st.header("Type Of Companies")

    df_typecode = pd.read_sql(
        'SELECT Code,Description FROM code WHERE Category="TypeOfEnterprise" AND Language="FR"', con)
    df_juridicform_type = pd.merge(
        df_juridicform, df_typecode, left_on='TypeOfEnterprise', right_on='Code')
    third_question = df_juridicform_type.groupby(
        ['TypeOfEnterprise', 'Description'], as_index=False).agg({'EnterpriseNumber': 'count'})

    fig3, ax3 = plt.subplots()
    ax3.pie(third_question['EnterpriseNumber'],
            labels=third_question['Description'], autopct='%1.1f%%', colors=['#db4c42', '#42dbbc'])
    plt.figure(figsize=(5,5))
    st.pyplot(fig3, transparent=True)


# Question 4
with tab4:
    st.header("Average Age of Compagnies")

    df_nace = pd.read_sql(
        'SELECT activity.EntityNumber,activity.NaceCode ,activity.NaceVersion,enterprise.StartDate FROM activity INNER JOIN enterprise ON enterprise.EnterpriseNumber=activity.EntityNumber', con)

    df_nace['StartDate'] = pd.to_datetime(df_nace['StartDate'])
    df_nace['year'] = df_nace['StartDate'].dt.year
    df_nace['Age'] = 2022 - df_nace['year']

    # Fetching the public official categories online
    url = 'https://www.inasti.be/fr/liste-des-divisions-et-nomenclature-dactivites-nace-bel-2008'
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, 'html.parser')
    table = soup.find_all('table', attrs={'class': 'alternating-rows'})
    lst = []
    for i in table[0].find_all('td'):
        lst.append(i.text)
    dct = {}
    i = 0
    for i in range(0, 176, 2):
        dct[lst[i]] = lst[i+1]

    columns = dct.keys()
    values = dct.values()

    df_codes = pd.DataFrame().assign(Activity=columns, Codes=values)

    df_nace['main_actv_code'] = df_nace['NaceCode'].astype(str).str[:2]

    df_nace_with_codes = pd.merge(
        df_nace, df_codes, how='left', left_on='main_actv_code', right_on='Codes')


    df_sector_mapping = pd.read_csv('mapping_sector_2008.csv')

    df_nace_with_codes['code_int'] = df_nace_with_codes['main_actv_code'].astype(
        int)

    # GRAPH 1
    fig4, ax = plt.subplots()
    ax.hist(df_nace_with_codes['year'], bins=100, color="green", edgecolor="darkgreen")
    ax.spines['bottom'].set_color('grey')
    ax.spines['top'].set_color('grey')
    ax.xaxis.label.set_color('grey')
    ax.yaxis.label.set_color('grey')
    ax.tick_params(axis='x', colors='grey')
    ax.tick_params(axis='y', colors='grey')
    plt.xlim(1940,2022)
    plt.xlabel('Year')
    plt.ylabel('Nbr of Company')
    
    st.subheader("Foundation year")
    st.pyplot(fig4, transparent=True)

    df_nace_with_codes_merged = pd.merge(df_nace_with_codes, df_sector_mapping, how='left', left_on='code_int', right_on='code_sector')

    fourth_question_letter_code = df_nace_with_codes_merged.drop(
        columns=['StartDate', 'main_actv_code', 'Codes', 'code_int'])

    df_2003 = fourth_question_letter_code[fourth_question_letter_code['NaceVersion'] == '2003']
    df_2008 = fourth_question_letter_code[fourth_question_letter_code['NaceVersion'] == '2008']   

    fourth_graph_2003 = df_2003.groupby(
        'title_sector', as_index=False).agg({'Age': 'mean'})
    fourth_graph_2003 = fourth_graph_2003.sort_values('Age', ascending=False)

    fourth_graph_2008 = df_2008.groupby(
        'title_sector', as_index=False).agg({'Age': 'mean'})
    fourth_graph_2008 = fourth_graph_2008.sort_values('Age', ascending=False)

    # GRAPH 2

    st.subheader("Average age per sector") 

    option = st.selectbox(
        'Please select the Nace Version:',('2008', '2003'))

    if option == '2003':

        fig6, ax = plt.subplots()
        ax.bar(fourth_graph_2003['title_sector'],fourth_graph_2003['Age'])
        plt.xlabel('Avg Age')
        plt.ylabel('Sectors')
        plt.xticks(rotation=90)

    else:
        fig6, ax = plt.subplots()
        ax.bar(fourth_graph_2008['title_sector'],fourth_graph_2008['Age'])
        plt.xlabel('Avg Age')
        plt.ylabel('Sectors')
        plt.xticks(rotation=90)

    figsix_new_labels = []

    for i in ax.xaxis.get_ticklabels():
        label = i.get_text()
        if len(label) > 120:
            figsix_new_labels.append(label[0:42])
        else:
            figsix_new_labels.append(label)

    ax.xaxis.set_ticklabels(figsix_new_labels)


    st.pyplot(fig6, transparent=True)


with tab5:
    df_locality = pd.read_csv('zip_lat_long.csv')
    df_address = pd.read_sql('SELECT EntityNumber,Zipcode FROM address', con)

    df_address.dropna(inplace=True)

    df_address['Zipcode'] = df_address['Zipcode'].str.replace('\D', '')
    df_address['Zipcode'] = df_address['Zipcode'].str.extract('(\d+)')
    df_address['Zipcode'] = df_address['Zipcode'].str.strip()
    df_address = df_address[~df_address['Zipcode'].isnull()]
    df_address['Zipcode'] = df_address['Zipcode'].astype(int)

    df_lat_long = pd.merge(df_address, df_locality, how='right',
                        left_on='Zipcode', right_on='PostCode')

    st.header("Map of Belgian Companies")

    st.map(df_lat_long.sample(frac=0.1), zoom=7)


with tab6:

    df_sector_mapping = pd.read_csv('mapping_sector_2008.csv')

    df_main_activity = pd.read_sql('SELECT EntityNumber,NaceCode FROM activity WHERE NaceVersion=2008 AND Classification="MAIN"',con)

    df_main_activity['NaceCode'] = df_main_activity['NaceCode'].str[:2]
    df_main_activity['NaceCode'] = df_main_activity['NaceCode'].astype(int)
    df_main_activity_sectorname= pd.merge(df_main_activity,df_sector_mapping,how='left',left_on='NaceCode',right_on='code_sector')
    df_main_activity_sectorname.drop_duplicates(inplace=True)
    ent_count_by_sector= df_main_activity_sectorname.groupby('title_sector',as_index=False).agg({'EntityNumber':'count'}).sort_values('EntityNumber',ascending=False)

    fig7,ax = plt.subplots()
    ax.barh(ent_count_by_sector['title_sector'],ent_count_by_sector['EntityNumber'])
    new_labels = []

    for i in ax.yaxis.get_ticklabels():
        label = i.get_text()
        if len(label) > 120:
            new_labels.append(label[0:42])
        else:
            new_labels.append(label)

    ax.yaxis.set_ticklabels(new_labels)
    

    plt.ticklabel_format(style='plain',axis='x')
    plt.xlabel("Nbr of companies")
    plt.ylabel("Sectors")

    st.subheader("Number of company per sector (As MAIN Activity)")

    st.pyplot(fig7, transparent=True)

with tab7:

    df_language = pd.read_sql("SELECT d.EntityNumber,d.Language,c.Description FROM denomination d LEFT JOIN code c ON d.Language = c.Code WHERE c.Category='Language' AND c.Language='FR' ",con)
    ent_language_count = df_language.groupby('Language',as_index=False).agg({'EntityNumber':'count'}).sort_values('EntityNumber',ascending=False)
    fig8,ax = plt.subplots()
    ax.bar(ent_language_count['Language'],height=ent_language_count['EntityNumber'],color=['black', 'red', 'green', 'blue', 'cyan'])
    plt.ticklabel_format(style='plain',axis='y')
    plt.xticks(ticks=[0,1,2,3,4],labels=['NL','FR','No Info','ENG','GER'])
    plt.xlabel('Language of Companies')
    plt.ylabel('Number of Companies')
    plt.tick_params(left=False, bottom=False)
    st.subheader("Number of Companies per languages") 
    st.pyplot(fig8, transparent=True)


with tab8:
    st.caption("(c) Ahmet Samil Cicek & Martin Velge - BeCode / Bouman 5")

